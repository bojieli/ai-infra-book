import Foundation
import Metal
import MetalPerformanceShaders

let output = CommandLine.arguments[1]
guard !FileManager.default.fileExists(atPath: output) else { fatalError("Use a fresh output directory") }
try FileManager.default.createDirectory(atPath: output, withIntermediateDirectories: true)
let device = MTLCreateSystemDefaultDevice()!
let queue = device.makeCommandQueue()!
func value(_ i: Int) -> Float {
    let x = UInt32(truncatingIfNeeded: i) &* 1664525 &+ 1013904223
    return Float(Int((x >> 16) % 97) - 48) / 64
}
func buffer(_ count: Int, _ offset: Int) -> MTLBuffer {
    let b=device.makeBuffer(length: count*4, options: .storageModeShared)!
    let ptr=b.contents().bindMemory(to: Float.self, capacity: count)
    for i in 0..<count { ptr[i]=value(i+offset) }
    return b
}
func save(_ name:String,_ object:Any) throws {
    let data=try JSONSerialization.data(withJSONObject: object, options:[.prettyPrinted,.sortedKeys])
    try data.write(to: URL(fileURLWithPath: output+"/"+name))
}
var results:[[String:Any]]=[]
for m in [1,32,256] {
    let k=512,n=512
    let a=buffer(m*k,20000),b=buffer(k*n,10000),c=buffer(m*n,0)
    let ma=MPSMatrix(buffer:a,descriptor:MPSMatrixDescriptor(rows:m,columns:k,rowBytes:k*4,dataType:.float32))
    let mb=MPSMatrix(buffer:b,descriptor:MPSMatrixDescriptor(rows:k,columns:n,rowBytes:n*4,dataType:.float32))
    let mc=MPSMatrix(buffer:c,descriptor:MPSMatrixDescriptor(rows:m,columns:n,rowBytes:n*4,dataType:.float32))
    let op=MPSMatrixMultiplication(device:device,transposeLeft:false,transposeRight:false,resultRows:m,resultColumns:n,interiorColumns:k,alpha:1,beta:0)
    func run(_ repeats:Int) -> (Double,Double) {
        let start=ProcessInfo.processInfo.systemUptime
        let cb=queue.makeCommandBuffer()!
        for _ in 0..<repeats { op.encode(commandBuffer:cb,leftMatrix:ma,rightMatrix:mb,resultMatrix:mc) }
        cb.commit();cb.waitUntilCompleted()
        precondition(cb.status == .completed)
        return ((cb.gpuEndTime-cb.gpuStartTime)/Double(repeats),(ProcessInfo.processInfo.systemUptime-start)/Double(repeats))
    }
    _=run(10)
    var times:[[String:Double]]=[]
    for _ in 0..<11 { let (gpu,wall)=run(50);times.append(["gpu_s":gpu,"wall_s":wall]) }
    let ap=a.contents().bindMemory(to:Float.self,capacity:m*k),bp=b.contents().bindMemory(to:Float.self,capacity:k*n),cp=c.contents().bindMemory(to:Float.self,capacity:m*n)
    var maxError=0.0
    for row in 0..<m { for col in 0..<n {
        var reference=0.0
        for inner in 0..<k { reference += Double(ap[row*k+inner])*Double(bp[inner*n+col]) }
        maxError=max(maxError,abs(reference-Double(cp[row*n+col])))
    } }
    precondition(maxError==0)
    results.append(["kind":"matmul","m":m,"k":k,"n":n,"samples":times,"max_abs_error_fp64":maxError,"reference_elements":m*n])
}
for mib in [16,64,256] {
    let size=mib*1024*1024
    let source=device.makeBuffer(length:size,options:.storageModeShared)!,target=device.makeBuffer(length:size,options:.storageModeShared)!
    let src=source.contents().bindMemory(to:UInt8.self,capacity:size)
    for i in 0..<size { src[i]=UInt8(truncatingIfNeeded:i &* 17 &+ 11) }
    func copy(_ count:Int) -> (Double,Double) {
        let start=ProcessInfo.processInfo.systemUptime
        let cb=queue.makeCommandBuffer()!;let blit=cb.makeBlitCommandEncoder()!
        for _ in 0..<count { blit.copy(from:source,sourceOffset:0,to:target,destinationOffset:0,size:size) }
        blit.endEncoding();cb.commit();cb.waitUntilCompleted();precondition(cb.status == .completed)
        return ((cb.gpuEndTime-cb.gpuStartTime)/Double(count),(ProcessInfo.processInfo.systemUptime-start)/Double(count))
    }
    _=copy(5);var times:[[String:Double]]=[]
    for _ in 0..<11 { let (gpu,wall)=copy(20);times.append(["gpu_s":gpu,"wall_s":wall]) }
    precondition(memcmp(source.contents(),target.contents(),size)==0)
    results.append(["kind":"copy","payload_bytes":size,"samples":times,"all_bytes_match":true])
}
try save("results.json",results)
try save("environment.json",["device":device.name,"unified_memory":device.hasUnifiedMemory,"recommended_working_set":device.recommendedMaxWorkingSetSize,"os":ProcessInfo.processInfo.operatingSystemVersionString,"matmul":"MPSMatrixMultiplication FP32","copy":"MTLBlitCommandEncoder shared buffers","scope":"Warm reused buffers. GPU command-buffer timestamps per operation; wall includes encoding and synchronization. Not DRAM counters."])
print("completed",results.count,"configurations")
