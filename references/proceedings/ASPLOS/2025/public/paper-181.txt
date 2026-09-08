                                         Velosiraptor: Code Synthesis for Memory Translation
                                                      Reto Achermann                                       Em Chu∗                                 Ryan Mehri∗
                                               University of British Columbia                              JuliaHub                                   Replit
                                                  Vancouver, BC, Canada                                Boston, MA, USA                        San Francisco, CA, USA

                                                                                Ilias Karimalis                             Margo Seltzer
                                                                        University of British Columbia                University of British Columbia
                                                                           Vancouver, BC, Canada                         Vancouver, BC, Canada
                                        Abstract                                                                  ACM Reference Format:
                                        Security is among the top concerns of operating system (OS)               Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo
                                                                                                                  Seltzer. 2025. Velosiraptor: Code Synthesis for Memory Transla-
                                        developers. A secure runtime environment relies on the OS
                                                                                                                  tion. In Proceedings of the 30th ACM International Conference on
                                        to correctly configure the memory hardware on which it
                                                                                                                  Architectural Support for Programming Languages and Operating
                                        runs. This is mission-critical as it provides essential security-         Systems, Volume 2 (ASPLOS ’25), March 30-April 3, 2025, Rotterdam,
                                        relevant features and abstractions that ensure the integrity              Netherlands. ACM, New York, NY, USA, 17 pages. https://doi.org/
                                        and isolation of untrusted applications running alongside                 10.1145/3676641.3711998
                                        each other. Configuring a platform’s memory hardware is
arXiv:2608.07966v1 [cs.OS] 8 Aug 2026




                                        not a one-off effort as designers constantly develop new
                                        mechanisms for translation and protection with different
                                        features and means of configuration. Adapting the OS code
                                                                                                                  1     Introduction
                                        to the new hardware is not only a manual, repetitive and time-            Today’s computer systems contain many memory protection
                                        consuming task, it may also introduce subtle, but security-               units (MPUs), memory management units (MMUs), and other
                                        critical bugs that break security and isolation guarantees.               memory hardware or features that mediate access to memory
                                           We present Velosiraptor, a system that automatically gen-              resources. A single memory access may traverse multiple
                                        erates correct, low-level OS code that programs the memory                hardware units until it reaches its destination. Generally,
                                        hardware of a machine. Velosiraptor leverages software syn-               those hardware components provide mapping functionality
                                        thesis techniques and exploits the domain specificity of the              that can be split up into protection and translation [6].
                                        problem to make the synthesis process efficient. With Velosir-               Protection determines if a specific memory access is per-
                                        aptor, developers write only a high-level description of the              mitted. This involves checking whether the input address is
                                        memory hardware’s mapping behavior and OS environment.                    valid and the access mode or source of the memory access is
                                           The Velosiraptor toolchain transforms this specification               permissible given the protection attributes (e.g., write, privi-
                                        into a verified implementation that can be linked directly                lege level, or a specific device). Translation is the process of
                                        with the rest of the operating system. Incorporating the OS               transforming the address of a memory access. Mapping is a
                                        environment into this process allows porting an OS to new                 partial function from an input address to an output address,
                                        hardware platforms without worrying about writing code                    i.e., the mapping attempt can fail due to an invalid address
                                        to configure the memory hardware. We can also use the                     or insufficient permissions.
                                        same specification to generate hardware components. This                     The OS must program all memory hardware units of the
                                        enables research in new translation mechanisms, freeing up                machine correctly, including the processor’s MMUs, the Sys-
                                        OS developers from manually writing OS code.                              tem MMU, and other memory translation and protection
                                                                                                                  units isolating individual hardware components to ensure
                                        CCS Concepts: • Software and its engineering → Virtual                    the security of applications [26–28]. This means that OS de-
                                        memory; Automatic programming; Functionality.                             velopers must have precise knowledge of all the memory
                                                                                                                  hardware and all its subtle differences in their features and
                                        ∗ Work done while at The University of British Columbia.                  configuration options. For example, the OS must set the right
                                                                                                                  permission flags or memory attributes in the page table entry.
                                                                                                                  Therefore, the developer has to manually write the low-level
                                                                                                                  OS code that programs the mapping hardware.
                                                                                                                     Unfortunately, writing code to configure memory hard-
                                        This work is licensed under a Creative Commons Attribution 4.0 Interna-   ware is not a one-time effort and can take weeks [54]. Modern
                                        tional License.
                                        ASPLOS ’25, Rotterdam, Netherlands
                                                                                                                  platforms have many different memory hardware units me-
                                        © 2025 Copyright held by the owner/author(s).                             diating access to and from various chip subsystems. Those
                                        ACM ISBN 979-8-4007-1079-7/25/03                                          units have a diverse set of features and means of configu-
                                        https://doi.org/10.1145/3676641.3711998                                   ration that the developer needs to understand. Thus, the
ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands             Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


developer has to spend a significant amount of time repeat-              • a qualitative demonstration of the functionality of the
ing the same task: reading the hardware manual and then                    generated memory hardware module and the adaption of
manually writing and debugging configuration code – a pro-                 the generated code to the OS environment (Section 6.5).
cess that easily introduces subtle bugs [34, 45, 46, 48–51]
amplified by the repetition. Any error in the configuration            2     Modeling Memory Hardware Behavior
sequence can break system security, allowing applications              Modern memory hardware is diverse in both the features
to inadvertently corrupt data or obtain unauthorized access            it provides (e.g., means of translation and protection) and
to resources of other applications.                                    how the hardware is programmed (e.g., registers and trans-
   We build upon previous work [5] and present Velosiraptor 1 ,        lation descriptors). For example, both Arm and x86 use an
a system that automatically generates correct memory con-              in-memory page table to define virtual-to-physical address
figuration code. In Velosiraptor, developers no longer need to         translation. They offer similar functionality but have differ-
manually and tediously write this code. Instead, they obtain           ent layouts. The Xeon Phi co-processor [36] uses an array
a behavioral specification of the memory hardware as part              of registers to control memory accesses to the host mem-
of the technical hardware manual, or they write a specifica-           ory. Despite their heterogeneity, they share many common
tion that closely matches the description in the manual. This          characteristics that allow for a common, abstract model that
behavioral specification defines how the memory hardware               expresses their mapping behavior. For example, determining
performs address mapping. The Velosiraptor toolchain then              if the hardware maps a given input depends on state that
constructs a model of the memory hardware and uses soft-               is stored either in registers or an in-memory data structure.
ware synthesis to automatically generate the OS code that              We use the term map to encompass both translation and
configures the memory hardware. The behavioral specifica-              access control. From the behavioral model, we define an op-
tion needs to be written once per mapping unit. Velosiraptor           erational model that captures the concrete state and software
then tailors the generated code to a target environment by             visible interface. Finally, we define the basic building block
using an OS specification that describes, for instance, the            and composition rules with well-defined semantics.
memory allocation functions or capability invocations.
   Velosiraptor leverages domain-specific knowledge to make            2.1    Behavioral Model
software synthesis efficient. Velosiraptor uses divide-and-
conquer to reduce the search space of candidate programs               Abstractly, all memory hardware units either successfully
by orders of magnitude, resulting in a negligible kernel com-          map an address or raise an exception. Thus, we can model
pilation time overhead. This makes Velosiraptor a viable ap-           map behavior as a partial function from an input address, an
proach to automatically generating correct, low-level, mem-            access mode (e.g., read, write, execute, . . . ), and the memory
ory hardware configuration code.                                       hardware state (e.g., register contents) to an output address.
   Velosiraptor also enables research into new memory trans-                     map :: 𝑖𝑛𝑎𝑑𝑑𝑟 → 𝑚𝑜𝑑𝑒 → 𝑠𝑡𝑎𝑡𝑒 ⇀ 𝑜𝑢𝑡𝑎𝑑𝑑𝑟
lation and protection mechanisms by generating a simulated             Input and output addresses may be ordinary memory ad-
hardware component from the same behavioral specifica-                 dresses or they may also contain source information, e.g.,
tion. This lets developers evaluate the utility of proposed, but       which core or device initiated the memory access. The set
non-existent memory hardware [15, 29, 40]. Researchers no              of possible access modes can be defined per mapping unit,
longer have to build a hardware implementation to evaluate             e.g., to include processor modes such as user and supervi-
the efficacy of a newly proposed translation and/or protec-            sor mode. The state includes everything that can influence
tion mechanism. Currently, Velosiraptor supports the Arm               translation (e.g., registers and in-memory data structures
Fast Models [10], a functionally accurate platform simulator.          such as page tables). The map() function produces an out-
   We make the following contributions:                                put address if and only if the state permits access to the
  • A methodology to efficiently synthesize code interfacing           input address under the current access mode. Mathemati-
    with memory hardware (Section 4 and Section 6.2),                  cally, the map() function produces an output address if and
  • a domain-specific language to concisely express the be-            only if the input values are part of the function’s domain:
    havior of memory hardware (Section 3),                             (𝑖𝑛𝑎𝑑𝑑𝑟, 𝑚𝑜𝑑𝑒, 𝑠𝑡𝑎𝑡𝑒) ∈ 𝑑𝑜𝑚(map). For example, the corre-
  • the implementation of Velosiraptor in Rust that uses Z3            sponding entry in the page table must be valid and have the
    for program verification (Section 5),                              right permission bits set, otherwise, an exception is raised.
  • a backend for Velosiraptor that generates memory hard-                We currently focus on the mapping behavior and leave
    ware modules for the Arm Fast Models (Section 5.6),                triggering a specific exception class (e.g., the distinction be-
  • a quantitative evaluation showing the effectiveness of the         tween a translation fault and a write fault) for future work.
    search space reduction and the efficiency of the synthesis
                                                                       2.2    Operational Model
    process (Section 6.3), and
                                                                       Figure 1 depicts the operational model of a mapping unit (we
1 Velosiraptor is a wordplay on VLSI – synthesis for hardware logic.   use this term to refer to any memory hardware component
     Velosiraptor : Code Synthesis for Memory Translation                                        ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands

                                    addmap()/setperms()/delmap()
                         Software                                                     of bits, stored in registers or memory locations and includes
                                                  interface operations
       data        load/store                                               control   all relevant parts that define the mapping behavior. For ex-
       plane                                  reg    mem mmio instr         plane
                           Input                      Interface                       ample, on x86, the page table defines the virtual-to-physical
                (inaddr,mode)                                state update             address translation, whereas the CR4 (control register 4)
                           map()                      reg   mem
       exception                    state query         State                         defines whether the mapping is enabled [37]. The control
               (outaddr,mode)
                          Output                                              Unit    interface of the mapping unit defines the transitions of the
         Figure 1. The behavioral model of a mapping unit.                            state machine. Each transition is atomic, takes a sequence of
                                                                                      arguments and an input state, and produces a well-defined,
  fn addmap ( va : vaddr , sz : size , f : flags , pa : paddr ,
                                                                                      new state. Examples include updating a page table entry,
2             s: State ) -> (s ': State )                                             writing the translation base register, or executing the tlbwr
    ensures forall v : vaddr , m : mode ::                                            instruction on the MIPS R4700 [35]. Formally, this is:
4     inrange (va ,sz , v ) == > ( translate (s ' , v ) == pa +( v - va )
        && ( allows (f , m ) <== > (v ,m ,s ') in dom ( map ) ) )
                                                                                                transition :: 𝑆𝑒𝑞<𝑎𝑟𝑔> → 𝑠𝑡𝑎𝑡𝑒 → 𝑠𝑡𝑎𝑡𝑒
6                                                                                     We expect that most transitions take zero or one machine-
   fn setperms ( va : vaddr , sz : size , f : flags , pa : paddr                      word-sized argument, representing the payload of load, store
8                s: State ) -> (s ': State )
     ensures forall v : vaddr , m : mode ::                                           or other instructions. A special init-transition defines the
10     inrange (va ,sz , v ) == > ( translate (s ' , v ) == translate (s , v )        bit pattern of the initial state. The control interface then
         && ( allows (f , m ) <== > (v ,m ,s ') in dom ( map ) ) )                    consists of a set of transitions and the init transition.
12
   fn delmap ( va : vaddr , sz : size , f : flags , pa : paddr                           In the model, the OS cannot access the state of the map-
14             s: State ) -> (s ': State )                                            ping unit directly. Instead, the OS interacts with the control
     ensures forall v : vaddr , m : mode ::                                           interface – the mapping unit’s public API. To change a unit’s
16     inrange (va ,sz , v ) == > (v ,m ,s ') not in dom ( map )
                                                                                      mapping behavior, the OS puts the state machine into the
     Listing 1. Synthesis target function specifications where                        desired state by applying the right sequence of atomic tran-
     map() refers to the map-function defined in Section 2.1
                                                                                      sitions. This notion becomes important in Section 4.3 as the
                                                                                      available state transitions correspond to the grammar of the
     that mediates memory accesses through address translation                        programs that are needed to configure the mapping behavior.
     or access control). The operational model of a mapping unit
     consists of three main components: map(), state, and interface                   2.2.3 Data Plane. Recall, that the mapping has two parts:
     (shown by the dark boxes in Figure 1). It resembles a state                      translation and access control. A boolean expression distin-
     machine where each state has a well-defined mapping be-                          guishes whether the map() function produces an error or an
     havior. The state consists of registers and memory locations,                    exception (we do not model different exception types).
     and the OS triggers state transitions by reading or writing                         We express access control checks as boolean predicates in
     special or MMIO registers or memory locations or executing                       conjunctive normal form. The conjuncts are boolean func-
     specific instructions. Similar to a network switch, the opera-                   tions defined over the input address, access mode, and state.
     tional model consists of a data plane and a control plane, but                   Output address computation occurs if, and only if, all the
     instead of processing network packets, it processes memory                       conjuncts evaluate to true; otherwise the unit raises an ex-
     accesses, i.e., load or store instructions or DMA transfers.                     ception. Formally, we express this as:
                                                                                                                          Û
                                                                                      (𝑎𝑑𝑑𝑟, 𝑚𝑜𝑑𝑒, 𝑠𝑡𝑎𝑡𝑒) ∈ 𝑑𝑜𝑚(map) ⇔        𝑝 (𝑎𝑑𝑑𝑟, 𝑚𝑜𝑑𝑒, 𝑠𝑡𝑎𝑡𝑒)
     2.2.1 Synthesis Target Specifications. The memory man-
                                                                                                                               𝑝 ∈𝑃
     agement subsystem must provide three functions: addmap                           If the input address is outside of the valid range or the access
     adds a new mapping from an input address range to an                             mode is not permitted, at least one of the conjuncts evaluates
     output address range with specified permissions, setperms                        to false, rendering the map() function undefined for the input
     changes the access permissions of an address range, and                          arguments. The formalization using the conjuncts helps us
     delmap removes a mapping. Listing 1 shows the correspond-
                                                                                      state the problem of synthesizing the correct configuration
     ing function signatures, which serve as the specifications for                   program for the mapping unit (Section 4.4).
     our synthesis targets. The predicate allows(f, m) defines
     whether the access mode is permitted given the supplied                          2.3   Composition of Building Blocks
     permission flags. The synthesis task is then to find an imple-
                                                                                      Given the diversity in memory hardware, we designed a
     mentation by finding a sequence of state machine transitions
                                                                                      methodology of basic building blocks and composition rules
     (i.e., interface interactions) that produces the goal state de-
                                                                                      from which we compose specifications hierarchically. This
     fined as post-conditions. Note, that there is an implicit post-
                                                                                      modular approach makes synthesis easier and more amenable
     condition ensuring that the behavior outside of the specified
                                                                                      to optimization [32]. After analyzing more than 12 different
     address range is not changed.
                                                                                      memory hardware units, we were pleasantly surprised that
     2.2.2 Control Plane. We model the control interface as                           we identified only one basic building block and two composi-
     a state machine. The state of a mapping unit is a sequence                       tion rules from which we could specify all of them.
ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands         Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


2.3.1 The Basic Building Block. The basic building block                   CR3
                                                                                  48
                                                                                             PML4                PDPT                Huge Frame
                                                                                                                                                   Page Table Level
                                                                                                        39                 30
is a segment that maps a contiguous input address range                  page directory                                                            output address
                                                                                                        21    PDirEntryTable
to a contiguous output address range. The output address                   0 21 frame           table
                                                                                                                                                   Building Blocks
                                                                                                                                                       segment
                                                                                                              PDirEntryFrame
range might be the ultimate result of a map or it might be                          frame                          ...               Base Frame
                                                                                            ... table        entry.pagesize=0         12           Composition Rules
an intermediate result, providing the address of the next                 PDir         PDirEntry                                                     static map
                                                                    30              frame
                                                                                                              PDirEntryTable         Page Table       Enumeration
unit in a structure such as the x86 tree-based page table.                                      table                           21
                                                                                                              PDirEntryFrame         Large Frame
                                                                                    frame       table
The segment has both a state and a control interface. The                 511                                entry.pagesize=1

input or output address range, i.e., the base address and size,        PDirEntryTable -> PageTable;        PDirEntryFrame -> LargeFrame;
may be either fixed (i.e., hardwired to a certain value) or            PDirEntry      = [ PDirEntryTable | PDirEntryFrame ];
                                                                       PDir           = [ PDirEntry; 512 ];
configurable (e.g., computed from the state). For example,
the Xeon Phi entry system memory page table [36] maps              Figure 2. Decomposition of the four-level x86_64 page table
a fixed input address range of 16 GB. In contrast, the x86         into basic building blocks and composition rules.
segment descriptor [37] allows mappings of different sizes,
and x86 page directory entries may map to the next-level
                                                                   components by following a page table walk. A walk begins
page table encoding the tree structure.
                                                                   with access to the base register (CR3) and then traverses
2.3.2 Combining Basic Building Blocks. Developers                  through a four-level radix tree (PML4, PDPT, PDIR, PTable)
combine segments using the composition rules. Each rule            as indicated by the dotted boxes of Figure 2. Having identi-
has well-defined semantics and dictates constraints on the         fied the structures we need, we next recursively decompose
composite state arising from the combined states of the basic      the components into building blocks: CR3 cannot be split
building blocks. Rules do not have state or control interfaces.    up further, so we model it as a segment unit. Each level in
Enumeration. Enumerations provide a way to create a                the tree is an array of entries each mapping a fixed, non-
structure akin to a C union from two or more segments. Each        overlapping part of the input address range. The page di-
variant of the enumeration is a segment that has the same          rectory allows the mapping of either a page table or a large
state bits, but it may interpret those state bits differently.     page (differentiated by the page size bit). Therefore, we use
For example, a page directory entry can map a large frame          the enumeration rule to combine two segments – one map-
or a page table, depending on whether the page-size bit is         ping a frame (PDirEntryFrame) and the other mapping the
set. Variants must be non-conflicting, i.e., the state must        page table (PDirEntryTable) – to form a page directory entry
unambiguously identify which segment description provides          (PDirEntry). Finally, the enumerations are then combined
the right interpretation of the state.                             using the static map composition rule to form the table.
StaticMap. A static map defines a table-like construct com-
posed of a collection of entries, each of which covers an in-      2.4      Mapping Unit Type Hierarchy
dependent, non-overlapping, and contiguous address range.          From the composition example above, we see that express-
Each entry in a static map may be either a segment or an           ing the mapping unit as a combination of segment units and
enumeration, but not another static map. In principle, Velosir-    composition rules is similar to a type or class hierarchy. In-
aptor supports entries of different types, but we have not         deed, each of the defined segment units and rule applications
encountered this in the mapping units we analyzed. Some            defines a type. The specification defines how the types are
part of the input address must specify which table entry           instantiated and how they are referenced by the units. Thus,
contains the mapping for the input address. Like the enu-          from the specification of the mapping unit, we can obtain
meration, the map links the state of the referenced segments       the type hierarchy. Further, by knowing the type hierarchy,
together, adding constraints on the combined state.                we can extract the structure of in-memory data structures
2.3.3 Composition Example. We use a simplified repre-              such as the two descriptor tables used in the example. Finally,
sentation of the four-level x86_64 virtual address translation     using the types we can reuse the basic building blocks in
as an illustrative example (we exclude segmentation and the        other mapping unit descriptions.
TLB for simplicity). From the manual [37], we learn that ad-
dress mapping accesses a four-level radix tree of in-memory        3      Specification Language
descriptor tables, a translation base register (CR3), and regis-   Developers write two specifications in the Velosiraptor Spec-
ters that control translation features such as physical address    ification Language: The first specification describes the map-
extension and whether the MMU is enabled (omitted in Fig-          ping behavior of the hardware using intuitive language con-
ure 2). The OS configures the mapping behavior by writing          structs for the concepts outlined in the previous section.
specific bit patterns into the registers or page table entries.    The second specification describes the runtime environment
   Figure 2 shows the decomposition of the x86_64 address          provided by the OS, e.g., memory allocation functions.
translation into Velosiraptor building blocks with the page           We explain the language constructs and how they relate to
directory shown in detail. We describe the behavior of these       the behavioral model using the X86_64 page directory from
     Velosiraptor : Code Synthesis for Memory Translation                                   ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands


     // PDir table as static map                                                 a page table that we express as a configurable segment. In
 2 staticmap PDir ( base : paddr )
                                                                                 x86, table entries mapping other tables have similar represen-
       {   maps [ PDirEntry ( base + i * PTABLE_ENTRY_SIZE )
 4                  for i in 0.. PTABLE_NUM_ENTRIES ]; }                         tations. To avoid duplication, Velosiraptor provides a notion
     // PDirEntry with two variants                                              of inheritance. On line 9, we specify the PDirEntryTable by
 6   enum PDirEntry ( base : paddr )                                             deriving it from the generic page table descriptor PTableDesc
       { PDirEntryTable ( base ) , PDirEntryFrame ( base ) }
 8   // PDir entry mapping a page table ( derived )                              (omitted) and specialize the addmap function (Line 10). Note
     segment PDirEntryTable ( base : paddr ) : PTableDesc {                      the type of the pa parameter here defines the type of the
10     synth fn addmap ( va : vaddr , sz : size , flgs : flags , pa : PTable )   next unit, i.e., PTable, effectively encoding the page table
          requires pa & ( BASE_PAGE_SIZE - 1) // ...
12   }                                                                           tree structure. The second variant maps a large frame. Thus,
     // PDir entry mapping a large frame                                         on line 14 we declare a segment unit (PDirEntryTable).
14   segment PDirEntryFrame ( base : paddr ) {
       state ( base : paddr ) {                                                  3.2   Specification Details
16        mem entry [ base , 0 , 8] {
             0 .. 1 present ,                                                    The Velosiraptor language has specific constructs to express
18           1 .. 2 writable , // bits 2..7 removed for space                    the concepts of the operational model (Section 2) and allows
             7 .. 8 pagesize , // bits 8..21 removed for space
20          21 .. 48 address ,                                                   developers to intuitively specify the mapping behavior.
       } }
22     interface ( base : paddr ) {                                              3.2.1 State Definitions. Recall, that the state is just a se-
          mem entry [ base , 0 , 8 ] {                                           quence of bits in the operational model. The state definition
24          Layout { /* same as state */ }                                       (line 15) assigns names to specific groups of bits of the state.
            WriteActions { interface . entry -> state . entry ; }
26          ReadActions { state . entry -> interface . entry ; }                 The state definition can be interpreted as declaring private
       } }                                                                       data members of a class. Logically, the state is divided into a
28     #[ pred ]                                                                 set of fields that correspond to individual registers or words
       fn valid () -> bool
30     { state . entry . present == 1 }                                          in memory. Register fields (declared with the reg keyword)
       #[ pred ]                                                                 have just a size, while in-memory fields (mem keyword) also
32     fn is_writable ( flgs : flags ) -> bool                                   have an address parameter and an offset. For example, line 16
       { flgs . writable == > state . entry . writable }
34                                                                               defines an 8-byte in-memory location, named entry, at offset
       fn translate ( va : vaddr ) -> paddr                                      0 from base. Registers or memory words may further contain
36       requires state . entry . pagesize == 1                                  groups of bits with specific semantic meanings. Developers
       { va + ( state . entry . address << LARGE_PAGE_BITS ) }
38                                                                               can define bit slices a..b, which assign names to consecutive
     synth fn addmap ( va : vaddr , sz : size , flgs : flags , pa : paddr )      ranges of bits from a to b (exclusive). Line 17 assigns bit slice
40     requires va == 0 && sz == LARGE_PAGE_SIZE                                 0..1 (i.e., bit 0) the name present, so it can be referenced by
       requires pa & ( LARGE_PAGE_SIZE - 1) == 0
42 } // end of PDirEntryFrame                                                    a semantically meaningful name.
     Listing 2. Simplified x86_64 Page Directory Specification                   3.2.2 Interface Definitions. The control interface defini-
                                                                                 tion (line 22) specifies the software-visible API and follows
                                                                                 a similar pattern to the state definition by assigning names
     Figure 2 and show the slightly simplified specification in                  to parts of the interface. Recall, that the operational model
     Listing 2. We omit parts of the state and interface description             does not permit directly accessing the state of the unit.
     and setperms and delmap for readability.                                       The interface is divided into a set of fields each of which
                                                                                 may have a layout (i.e., bit slices) and a set of actions (i.e.,
     3.1   Language Overview                                                     ReadActions and WriteActions) that specify how the state is
     Listing 2 shows the definition of two basic building blocks                 updated. Each field is either: 1) an in-memory location (mem)
     and two composition rules that correspond to the x86_64                     that is an overlay of an in-memory state field, 2) a memory-
     page directory shown in Figure 2. Line 2 defines the page                   mapped register (mmio), 3) a non-memory-mapped register
     directory (PDir) as a static map. The base parameter is the                 (reg), or 4) an instruction (instr).
     address where the PDir is allocated in memory. We use list-                    Action blocks contain a list of data transfer actions that
     comprehension notation to express that the PDir is a table of               atomically execute whenever the interface field is accessed.
     PTABLE_NUM_ENTRIES=512 entries. We instantiate each entry                   Lines 25 and 26 show the data transfer between the interface
     at an address relative to the base parameter to associate                   and the state where the state and interface variables refer
     individual entries with the full table.                                     to the current unit instance. Note that for fields defined with
        An entry in the PDir has two variants, so we use the enum                mem, the actions are restricted to the corresponding mem state
     keyword to define an enumeration (PDirEntry) on line 6. The                 fields. Register-backed interface fields may trigger multiple
     enumeration lists the variants and constrains the variant’s                 non-conflicting updates to the entire state
     parameters by binding them to the corresponding parameter                      As an optimization, developers may omit the layout and
     of the enumeration (base parameter). The first variant maps                 action blocks if there is a state field with the same name and
ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands       Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


kind. In that case, the interface field acts as an overlay and         OS Spec                                                       Verify Query   SMT
                                                                                                        SMT Model        sat?
                                                                                                                                6                   Solvers
inherits the same layout as the state field and the default            Unit Spec           Feasibility Query      sat?
                                                                          1
actions will simply pass through all reads and writes.                                                                Correct?         Yes!
                                                                                            Solution     Query           Veriﬁer      Program
                                                                       parser               Exists?      Cache                  Next
                                                                                                    3                         5
                                                                     Parse Tree                                      Candidate    Program
3.2.3 Methods. Methods, defined with the keyword fn,                                             Feasibility          Program     Generator
                                                                                                   Check                       4
contain expressions to compute a value and specify the map-                        Operational                 Extract Goal
                                                                   Type checker                                                            Predicates
                                                                                     Model 2                    Conditions
ping behavior. They can access the state directly through         Velosiraptor                                                      Optimizer
                                                                                   Code Generator
the state variable referring to the state of the current unit          Hardware Module      Interface Bindings addmap/setperms/delmap
instance (such as the this pointer). Methods can further                             Figure 3. Synthesis Oveview
specify requires clauses that express pre-conditions of the
method, which serve as constraints in the synthesis process.
Methods effectively create named expressions that can call
each other (we disallow loops and recursion). There are three    resulting programs are correct, because Velosiraptor veri-
special method classes.                                          fies the synthesized programs against the model and their
mapping Predicates. As outlined in the behavioral model,         specification, i.e., the post-conditions stated in Listing 1.
the mapping function is defined only if all conjuncts are           We start by defining our synthesis problem, followed by
true. Developers define such conjuncts by tagging a function     an overview of the synthesis process. We then describe the
returning a boolean value with the #[pred] decorator. This       generation of candidate programs and the grammar that
explicitly names the conjuncts: e.g., valid on line 29 states    we use to construct them. Finally, we present techniques
that the entry is valid if the present bit is set.               to reduce the search space and handle caches, maintenance
Translation Function. The translate() function on line           operations, and barriers.
35 defines how the output address is computed. The requires
clauses further establish the condition for the variant (i.e.,   4.1     Formulating the Synthesis Problem
the page size bit must be one).                                  Velosiraptor solves the synthesis problem of finding a se-
Synthesis Target Functions. Only the synthesis targets           quence of control interface invocations that move the state
of Listing 1 are declared as synth fn. They define additional    machine from an arbitrary start state into an end state that
constraints on the synthesis target through pre-conditions,      has the desired mapping behavior, i.e., satisfies the post-
and have the implicit post-conditions shown in Listing 1.        condition of the synthesis target (Listing 1).
Line 39 shows addmap with the pre-conditions that establish        Synthesis Problem: Let 𝑠 0 represent an arbitrary start-
constraints on the alignment of the frame and the unit’s           ing state and 𝑎𝑟𝑔𝑠 represent the arguments to the higher-
supported mapping range, i.e., the mapping is a large frame.       level function. Further, let assms be the constraints on
                                                                   valid states, and goal be the post-condition of the current
3.3   Environment Specification                                    synthesis target. Find a sequence of state transitions 𝑜𝑝
                                                                   that satisfies the following predicate.
Operating systems have different personalities, so the run-
                                                                    ∀𝑠 0, 𝑎𝑟𝑔𝑠 :: assms(𝑠 0, 𝑎𝑟𝑔𝑠) ⇒ goal(op(𝑠 0, 𝑎𝑟𝑔𝑠), 𝑎𝑟𝑔𝑠)
time environments (e.g., functions for allocating and freeing
memory, types, and means to access registers) vary. For exam-       In other words, for any valid starting state and input ar-
ple, Linux allocates memory for the translation descriptors      guments, applying the state transitions of the candidate pro-
using page_alloc, whereas on capability-based systems (e.g.,     gram results in a state that has the desired mapping behavior.
seL4 [39] or Barrelfish [16]), applications perform alloca-      The assms define assumptions on the initial state and the
tions through a sequence of capability operations, but the       input arguments, e.g., the bit widths and alignments of ad-
kernel still needs to format the translation descriptors cor-    dresses, and goal are the post-conditions stated in Listing 1.
rectly. The description language allows developers to specify
the runtime environment by declaring external types and          4.2     Synthesis Overview
function signatures that the OS provides. If changes can be      Figure 3 shows the overview of the synthesis process. 1
applied only indirectly (e.g., through capability operations)    The input to the synthesis process is a specification of the
the developer provides the corresponding invocation to the       mapping unit in the Velosiraptor specification language (Sec-
addmap, setperms, and delmap .                                   tion 3). 2 From the specification, we create the operational
                                                                 model of the mapping unit including its state and control in-
                                                                 terface. 3 We encode the operational model in smtlib2 [14]
4     Program Synthesis Methodology                              using bit vector logic and perform a feasibility check using
Velosiraptor uses hierarchical software synthesis to auto-       the SMT solver. 4 The program generator starts construct-
matically generate correct implementations for the addmap,       ing candidate programs, following a grammar derived from
setperms and delmap functions (our synthesis targets). The       the control interface. 5 We iterate through the candidate
Velosiraptor : Code Synthesis for Memory Translation                           ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands


programs until we find one that satisfies the goal or we ex-        Program Structure. The grammar that we use to construct
haust the search space. 6 The verifier encodes the candidate        candidate programs already constrains what programs we
program into an SMT query and uses an SMT solver to check           can consider. This not only reduces the search space but also
whether it satisfies the goal conditions derived from the post-     enables the possibility of merging two programs, a property
conditions. For efficiency, we apply various domain-specific        that we leverage in the following technique.
optimizations that we describe in Section 4.4.                      Divide-and-Conquer Synthesis Goal. We leverage the
                                                                    definition of a successful map to split up the goal predicate,
4.3   Generating Candidate Programs                                 solve for each subgoal independently, and merge the partial
From the specifications of addmap, setperms, and delmap, Velosir-   programs. In Section 2, we defined a successful map oper-
aptor automatically generates possible implementations called       ation as correctly calculating the address and satisfying a
candidate programs. With no constraints, this quickly leads         conjunction of predicates. The specification language (List-
to an explosion in the size of the search space. We use a           ing 2) already follows this division. We further rewrite all
domain-specific property that lets us constrain the search          predicates into conjunctive normal form to enable further
space. Recall, that the control interface of the mapping unit       predicate splitting. We generate partial candidate programs
defines the software-visible API (i.e., the interface fields as     and check whether they satisfy the subgoals. Finally, we
the function calls, and the bit slices are the argument val-        merge the partial candidate programs to obtain the candi-
ues). Thus, the control interface defines the grammar that          date program and verify it against the original goal.
generates the candidate programs.                                   API Reduction. The subgoal predicates may not use all bits
Grammar Description. At the top level, a candidate pro-             of the state. For example, the valid predicate of Listing 2
gram is a sequence of one or more atomic API invocations            depends only on the present bit. Thus, instead of taking the
chosen from the defined control interface fields. Each API          entire control interface as the API, we reduce it to include
invocation is either a read or a write that will trigger the        only the relevant parts by performing the following steps.
corresponding ReadActions or WriteActions. The API invo-            First, we create the subset of the state that is relevant to the
cation consists of three parts: 1) initialize the argument value    current goal (i.e., parts of the state that are referenced in the
with zero, or read the current value from the control interface.    goal predicate). Then we identify the parts of the interface
2) update the argument value by setting the values of the           that can change any of the relevant parts by looking at the
corresponding bit slices. 3) perform a read or write with the       ReadActions and WriteActions blocks. This is a form of back-
constructed argument value. The values of the bit slices are        projection of the bit slices of the interface onto the state. This
set based on an expression that may involve the high-level          drastically reduces the grammar of the candidate programs
function parameters (e.g., address or size), binary operators,      to only 10-100 candidate programs per subgoal.
masks, or symbolic values.                                          Expression Reduction. The divide-and-conquer approach
Program Generation. Intuitively, the program generator              produces a set of subgoals that may have simple boolean ex-
starts by iterating over possible distinct combinations of          pressions such as 𝑒𝑛𝑡𝑟𝑦.𝑝𝑟𝑒𝑠𝑒𝑛𝑡 == 1. From the expression,
API invocations starting with the smallest possible candidate       we can extract various properties such as whether the re-
programs and then recursively expanding them. For example,          turned value is a boolean or address, whether any parameters
assuming a mapping unit with two registers interface fields         of the synthesis target are accessed, the size of the bit slice
𝐴 and 𝐵, the program generator starts considering programs          in bits, or whether the comparison is a constant expression.
of the form [A,B], [AA,AB,BA,BB], ... For each of the API           This lets us reduce the possible expressions. For example, if
interactions, the program generator constructs all possible         the expression does not refer to any of the arguments, we
expressions that update the argument value, initializations,        can exclude those from the list of possible expressions.
and invocation type. The number of possible programs grows
factorially in the size of the interface.                           4.5   Tree-Based Divide-and-Conquer
                                                                    Instead of simply combining all partial programs of the con-
4.4   Search Space Reduction                                        juncts, we construct a balanced binary tree structure. The
Simply generating all possible programs is impractical, so we       idea behind this is to filter wrong partial programs early
introduce domain-specific search space reduction techniques         to reduce the number of possible combinations. Consider
to make the synthesis process tractable.                            an example with four conjuncts 𝐴, 𝐵, 𝐶, 𝐷 with 10 candidate
State Reduction Through Decomposition. As outlined                  programs each, and 50% of the possible programs for each
in Section 2.3, we decompose complex mapping units into             subgoal satisfy the subgoal. Combining all of them in one
basic building blocks and composition rules. This reduces           step (𝐴 ∧ 𝐵 ∧ 𝐶 ∧ 𝐷) produces 4 × 10 + 54 = 665 programs to
the state and the interface by splitting the mapping unit into      check. However, with the tree structure (𝐴 ∧ 𝐵) ∧ (𝐶 ∧ 𝐷),
smaller pieces. For example, instead of considering an MMU          the number of programs drops to 2 × (4 × 10 + 52 ) = 94 for
with its multi-level page tables and registers in its entirety,     the leaf level, plus another 132 = 169 candidate programs on
we can focus on a single page-table entry at a time.                the middle level (with 50% satisfiability). This results in only
     ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands       Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


     size_t PDirEntryFrame_do_map ( PDirEntryFrame_t * unit ,         generate a type with functions to set and extract bit slice val-
          vaddr_t va , size_t sz , flags_t flgs , paddr_t pa ) {      ues (e.g., PDirEntryFrame_entry_present_set). The synthe-
2      // pre - condition check : ( pa & 0 x1fffff ) == 0 x0
       if (!((( pa & 0 x1fffff ) == 0 x0 ) ) ) { return 0 x0 ; }      sized program then prepares the argument value v and then
4      // configuration sequence                                      invokes the control interface (e.g., PDirEntryFrame_entry__wr).
       PDirEntryFrame_entry_t v = PDirEntryFrame_entry_new (0) ;      From the instantiated composition rules, the code generator
6      v = PDirEntryFrame_entry_address_set (v ,
              (( pa >> 0 x15 ) & 0 x7ffffff ) ) ;                     emits the corresponding code following a template. Finally,
8      v = PDirEntryFrame_entry_ps_set (v , 0 x1 ) ;                  the output is adapted to the OS environment. The code gen-
       v = PDirEntryFrame_entry_present_set (v , 0 x1 ) ;             erator finds the functions in the OS environment using the
10     v = PDirEntryFrame_entry_rw_set (v , flgs . writable ) ;
       // write the entry                                             corresponding type signature.
12     PDirEntryFrame_entry__wr ( unit , v ) ;                           The generated code follows a similar pattern to that found
       return LARGE_PAGE_SIZE ;                                       in Linux, seKVM [42], seL4 [39], and Barrelfish [16]. For
14   }
                                                                      example, Velosiraptor generates functions that walk the page
     Listing 3. Velosiraptor-generated Code for Mapping a Frame       tables, allocate and free memory for page tables, and write
     in the simplified x86 Page Directory from Listing 2.             the corresponding page table entries as shown in Listing 3.
                                                                      Similarly, Velosiraptor-generated code also includes types
     263 programs to check compared to the 665 programs that          for the different unit types as seL4 and Barrelfish do with
     arise from brute force search                                    its capability types or Linux and seKVM with their pmd_t,
                                                                      pud_t, etc, respectively.
     4.6   Caches and Barriers
     So far, we have assumed that interface interactions imme-        5     Implementation
     diately update the state and become visible to the mapping
                                                                      We describe the details of the Velosiraptor implementation
     function. Unfortunately, this is not always true. Stores may
                                                                      starting with an overview of the toolchain implementation
     end up in write-buffers, caches, or even get reordered delay-
                                                                      and how we encode the SMT queries. We then explain our
     ing the effect of the interface interaction.
                                                                      query scheduling and hardware generation backends, and
     Multi-Phase Synthesis. Velosiraptor handles cached or de-
                                                                      show how Velosiraptor helps developers write specifications.
     layed updates by extending the mapping unit model and
     the program generator to express write buffers and caches.
                                                                      5.1 Toolchain Overview
     However, instead of directly including cache operations and
     barriers in the synthesis process, we pursue a multi-phase       We implement Velosiraptor in Rust and use the Z3 SMT
     approach. The first phase operates as explained before and       solver [25]. The main components are the specification pars-
     produces a program that satisfies the goal under the assump-     ing, the intermediate representation of the mapping modules,
     tion that updates become visible immediately. The second         the synthesizer and the program generator, and backends for
     phase takes the output program as a starting point and starts    code generation for OS code and hardware components. We
     inserting barriers and cache operations. The new candidate       run the Z3 SMT solver as multiple standalone processes to
     programs are then verified against the extended model.           leverage parallelism. Velosiraptor sends smtlib2 [14] formulas
     Modeling Cache Operations. Instead of applying the up-           to the Z3 process and reads the results over a pipe.
     dates directly to the state, the extended model maintains a         The toolchain currently supports generating OS code in C
     list of outstanding write operations on the interface fields.    and Rust and generating hardware components for the Arm
     Read operations bypass this list and still return the current    Fast Models Simulator. We leave the generation of Verilog
     interface value directly. We add additional operations for       or other hardware description languages for future work.
     cache maintenance and barriers to the set of possible API
     interactions that make sure all previous API interactions        5.2    Encoding the Mapping Unit Model in SMT
     have been successfully executed.                                 Velosiraptor converts the mapping unit specification into
                                                                      SMT formulas (smtlib2 [14]) that can be evaluated by an
     4.7   Code Generation                                            SMT solver. The generated formulas can be divided into 1) a
     The code generator takes the mapping unit specification, the     prelude that defines types, 2) a representation of the mapping
     synthesized sequences of interface interactions, the OS envi-    unit model including its state and interface, and 3) queries
     ronment specification, and produces the corresponding C or       that verify the candidate programs against the current goal.
     Rust source code that implements the addmap, setperms, and       Type Encoding. Each mapping unit has a specified input
     delmap functions. Listing 3 shows the generated code for set-    and output bit width it supports. These bit widths define
     ting up a frame mapping for the simplified x86 page directory    the maximum values for the vaddr, paddr, and size types
     from Listing 2. For each of the defined building blocks and      of the specification language. We declare a new typed term
     composition rules, the code generator declares a type (e.g.,     containing a bit vector of length 64 and a boolean function
     PDirEntryFrame_t). For each field in the control interface, we   constraining the supported range of the values.
Velosiraptor : Code Synthesis for Memory Translation                                ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands


Mapping Unit Encoding. The encoding of a mapping unit                   ( push )                           ; new assertion set
                                                                   2 ( declare-const svar !0 Num_t ) ; define symbolic variable
model closely follows the language constructs (Listing 2) and
                                                                        ; current candidate program for map
the model outlined in Section 2. We assert the model only          4 ( define-fun map (( st0 Model_t ) ( va VAddr_t ) ( sz Size_t )
once once for each solver instance.                                                              ( flgs Flags_t ) ( pa PAddr_t ) ) Model_t
   We declare a new type containing a bit vector for each of       6       ( let ( st1 ( Model.IFace.pte.set ! st0 ZERO ) )
                                                                           ( let ( st2 ( Model.IFace.pte.present.set ! st1 symvar !0) )
the state and interface fields and functions providing acces-      8       ( let ( st3 ( Model.IFace.pte.wr ! st2 ) ) st3 ) ) ) )
sors to insert or extract the bit slices. Then we combine the           ; assert post-condition of map
field definitions into data types for the interface and state,     10   ( assert ( forall (( st !0 Model_t ) ( va VAddr_t ) ( pa PAddr_t )
                                                                                               ( sz Size_t )     ( flgs Flags_t ) )
and combine the interface and state datatypes into the model.      12                (= > ( map.assms st !0 va sz flgs pa )
For the ReadActions and WriteActions we define a function                                   ( translate.result ( map st !0 va sz flgs pa )
with the corresponding state updates. We declare functions         14                                               va sz flgs pa ))))
                                                                        ( check-sat )                 ; check satisfiability
for predicates defined on the state, including the defined         16   ( get-value ( svar !0) ) ; obtain value of symbolic variable
methods in the mapping unit specification, pre-conditions,              ( pop )                       ; drop the current assertion set
and other assumptions such as type constraints.                               Listing 4. SMT query to verify candidate programs
Write Buffers. To model caches and write buffers, we use
Z3’s internal list theory. This adds a list of interface invoca-
tions with the corresponding arguments to the model state.              a variable for the state, assert all mapping predicates, and
Executing the WriteActions block just adds the operation to             then ask the SMT solver to check satisfiability. If it is not, we
the list. Cache maintenance operations or barriers will then            extract the unsat-core from the SMT output, which shows
trigger the execution of the corresponding WriteActions                 which mapping predicates are conflicting.
block of the operations in the list.
                                                                        5.5    Query Scheduling and Caching
5.3   Verifying Candidate Programs                                      Velosiraptor leverages caching and scheduling techniques
To verify the candidate programs, we create a new assertion             to reduce the number of queries executed, thus decreasing
set and reuse the base model stated above. This enables                 synthesis time. We execute queries asynchronously to give
checking the satisfiability of the current goal without re-             more flexibility in scheduling them. Query execution stops
instantiating the model again. Listing 4 shows this query.              as soon as we find a program that satisfies the goal.
   First, we convert the implementation of the current candi-           Query Caching. Before sending a query to the SMT solver,
date program into an SMT function (Line 4) that takes the               Velosiraptor checks whether it already exists in the query
initial model state plus arguments and produces a new model             cache. If it does not, we add the query to the cache, mark the
state. The body performs the sequence interface actions to              entry as pending, register the query, execute it, and update
update the model. Secondly, we assert (Line 10) that for all            the entry once the query is finished. If the query is in the
possible initial states and arguments, the candidate program            cache, we either return the cached result or register the query
satisfies the goal condition for the end state. We chose to use         if the entry was pending. This avoids evaluating duplicate
the forall-style instead of the negated exists, because it              queries during the synthesis process.
allows us to directly obtain the value of symbolic variables.           Prioritizing Queries. We organize the execution of the SMT
Finally, we check whether the assertion holds (Line 15).                queries for the candidate programs as a tree (see Section 4.4).
                                                                        The query scheduler assigns priorities to the SMT queries
5.4   Use of SMT Output during Synthesis                                based on their position in the tree. The root has the highest
Velosiraptor uses the output of the SMT solver in three ways.           priority, and the leaves have the lowest priority. The intuition
As described before, we use it to check whether a program               behind this strategy is to prioritize the verification of more
satisfies the goal. In addition, we use it for obtaining scalar         complete programs and thus quickly bubble up candidate
values and detecting conflicting conditions.                            programs in the tree. Ideally, this means that not all queries
Obtaining Scalar Values. During synthesis, we encounter                 of the lower levels have to be executed.
expressions with unknown constants (e.g., addr << ?). We
declare a symbolic variable for it (Line 2). The SMT solver             5.6    Hardware Generation
then tries to find a satisfying assignment to all variables             Velosiraptor features a proof-of-concept hardware generation
including unknown constants. If the SMT solver succeeds,                backend that produces a simulated mapping unit that runs
we can extract the assigned value from the SMT output (Line             on the Arm Fast Models platform. This platform allows for
16) and replace the unknown constant in the expression with             functional, but not cycle-accurate, simulation of a hardware
the concrete value (e.g., addr << 12).                                  platform. In the Arm Fast Models, a platform is composed of
Conflicting Conditions. As part of the synthesis process,               multiple modules that are instantiated and their ports (e.g.,
we check whether the model itself is satisfiable, i.e., there           memory buses or interrupt lines) connected. Each module
is a state that satisfies all mapping predicates. We define             is described as a LISA+ [9] file, a domain-specific language
ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands         Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


built on top of C++. The Arm Fast Models toolchain then                     Configurations                 Results [ms]
processes all LISA+ components and dependencies to build            Name                   # Units   Programs Time P50 Time P95
                                                                    Simple Page Table 3U+ 2F+ 7S 9M+ 4P+ 3U       151ms     163ms
an executable simulator binary.
                                                                    x86_32 Page Table 7U+ 5F+38S 39M+16P+ 9U      561ms     582ms
   Velosiraptor generates a LISA+ file for the mapping unit         x86_64 Page Table 13U+ 8F+91S 72M+32P+18U 1,137ms 1,171ms
and a C++ implementation of the behavior for each unit              Arm MPU            1U+ 7F+22S 9M+ 7P+ 3U      750ms 1,129ms
defined in the specification file. The mapping unit module has      Xeon Phi SMPT      2U+ 1F+ 3S 4M+ 3P+ 0U       99ms     112ms
two upstream and downstream ports: two for the data plane           Simple Segment     1U+ 1F+ 2S 4M+ 0P+ 3U       32ms      37ms
                                                                    Variable Segment   1U+ 2F+ 5S 9M+ 4P+ 3U      453ms     525ms
(memory accesses), one for the control interface (registers),
                                                                    Medium Segment 1U+ 4F+18S 15M+ 5P+ 3U         824ms 1,024ms
and one for emitting memory accesses when the unit reads            Assoc Segment      1U+ 4F+ 6S 14M+ 4P+ 3U 1,058ms 4,475ms
in-memory descriptors. The C++ implementation of each               x86 Segmentation 1U+ 2F+16S 17M+ 5P+ 3U 12,445ms 12,683ms
building block and composition rule is generated directly           R4700 TLB          3U+ 8F+13S 17M+ 0P+ 7U 2,249ms 2,433ms
from its specification; there is no synthesis required.             Linux Ubuntu                 –          – 153,831ms 154,352ms
   The generated LISA+ registers the map() function of the         Table 1. Synthesis Times and Complexities. The unit column
top-level unit as the handler for incoming memory accesses.        shows the size of the specification in terms of basic build-
During the mapping process, the code path follows the type         ing blocks and composition rules (U), the total size of the
hierarchy of the specification, evaluating and calling the         interface (F), and the number of bit slices (S). The program
map() function of the next unit, if permitted, or returning an     column shows the length of the synthesized programs for
error. Ultimately, the output address is returned to the caller,   the addmap (M), setperms (P), and delmap (U) functions.
and the incoming memory access is updated. On error, the
simulator raises an exception at the originating CPU core.
   When describing a platform, the developer instantiates the      Methodology. We measure the runtime of the synthesis and
mapping unit module and connects its ports to the memory           code generation for the translation hardware descriptions
bus of a processor core and a memory module simulating             shown in Table 1. The units column shows the complexity of
RAM. Multiple mapping unit modules can be connected seri-          the description. This has a direct correlation with the size of
ally, or different address ranges can be translated by different   the grammar for the synthesized programs, larger numbers
mapping unit modules. This enables the developer to set up         indicate a bigger search space. We also measure the compila-
complex memory hierarchies and translation schemes.                tion time of the Ubuntu Linux kernel v6.2.0 (default Ubuntu
                                                                   configuration, no modules, using 28 hardware threads).
6     Evaluation                                                   Results. Table 1 shows the median and 95th percentile run-
We evaluate Velosiraptor using quantitative and qualitative        times over 100 runs. Some of the hardware (e.g., Xeon Phi
scenarios to answer the following questions:                       SMPT) does not support unmapping and/or access control
                                                                   so no program is generated. The measurements show that
 • How quickly does Velosiraptor synthesize code, and how
                                                                   Velosiraptor runtime is negligible relative to the kernel compi-
   well does synthesis scale? (Section 6.2)
                                                                   lation. For example, code synthesis for the x86_64 page tables
 • How much does each optimization improve runtime?
                                                                   takes about one second, whereas the entire kernel build takes
   (Section 6.3)
                                                                   more than 154 seconds. We see that x86 segmentation has a
 • How well does the hardware software co-generation
                                                                   significantly higher runtime compared to the x86_64 page
   work? (Section 6.4)
                                                                   tables, despite similar search space size (Section 6.3). The
 • How easily can Velosiraptor be integrated into operating
                                                                   page tables are very amenable to our divide-and-conquer
   systems? (Section 6.5)
                                                                   approach resulting in many small subproblems, whereas the
 • How does the performance of the generated code com-
                                                                   x86 segmentation has a complex expression for the output
   pare to hand-written code (Section 6.6).
                                                                   address and limit calculations that cannot be further split.
                                                                      We see higher variability in the runtime for specifications
6.1   Evaluation Setup
                                                                   that involve variable mapping ranges (i.e., Arm MPU, Vari-
We run our evaluation on an Intel Xeon W-2275 processor            able, Medium and Assoc Segments). Upon further examina-
with 14 cores with two hyperthreads each. The host OS              tion, we observe a bimodal runtime distribution for these
is Ubuntu 24.04 LTS with Linux kernel 6.5.0, and we use            specifications. Investigation of the generated SMT queries
Z3 version 4.10.2 as the SMT solver. We set the number of          reveals a nested forall quantifier involving symbolic vari-
workers equal to the number of cores.                              ables. Solving these queries may take a few milliseconds or
                                                                   can take several seconds to solve, contributing to runtime
6.2   Velosiraptor generates code quickly                          variability and comprising almost half of the total runtime.
We evaluate Velosiraptor synthesis and code generation per-        Discussion. Velosiraptor provides a viable approach for auto-
formance showing that its runtime is sufficiently small to be      matically generating low-level OS code without significantly
practically incorporated into kernel compilation.                  affecting kernel build time.
Velosiraptor : Code Synthesis for Memory Translation                       ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands


  Spec              No Opts +IfaceOpt +StateOpt +ExprOpt +Tree   component and the corresponding OS code. We boot our
  Simple Page Table      23        23         5        3     3
                                                                 own simple, firmware-like image containing the Velosirap-
  x86_32 Page Table      37        37        18       10    10
  x86_64 Page Table      38        38        21       13    13   tor-generated code on the simulated hardware platform. We
  Arm MPU                38        38         7        5     5   then perform a sequence of loads and stores to the region
  Xeon Phi SMPT           7         7         2        1     1   translated by the generated hardware component. We re-
  Simple Segment          4         4         2        1     1   configure the memory hardware and repeat the test while
  Variable Segment       33        33         7        5     5
                                                                 checking whether we observe the expected behavior.
  Medium Segment         37        37        13       10    10
  Assoc Segment          38        38        12        9     9   Results and Discussion. All cases booted successfully and
  x86 Segmentation       38        38        18       13    13   we observed the expected behavior. Velosiraptor is capable
  R4700 TLB              38        37        11        9     9   of generating both a simulated hardware component and
Table 2. Calculated search space sizes (log10) with cumula-      OS code from the same description. This is a promising re-
tive optimizations.                                              sult as it enables further research in mapping hardware and
                                                                 may reduce the effort of FPGA developers to use mapping
                                                                 hardware in their FPGA-accelerated applications.
6.3   Ablation Study of Optimizations                            6.5   Velosiraptor can be used in a real OS
We now evaluate how effectively each optimization reduces        We demonstrate that Velosiraptor can be used in an existing
the search space size.                                           OS code base by integrating the generated code into the
Methodology. We run Velosiraptor on the descriptions shown       Barrelfish OS [16], including a monolithic setting.
in Table 1 and selectively turn on the optimizations outlined    Methodology. We take the x86_64 page table specification
in Section 4.4 and calculate the search space of possible can-   and generate code for three OS environments:
didate programs. Due to the search space size, we are unable     1) Monolithic: The code can directly access the registers and
to run synthesis without certain optimizations and therefore     in-memory data structures that define the translation behav-
do not measure synthesis time.                                   ior. It also allocates and frees memory for the page tables.
Results. Table 2 shows the calculated search space sizes (in     2) uKernel supervisor: The generated code can also directly
base-10 logarithm) for the different, cumulative optimization    access the registers and in-memory data structures, but it
levels. Enabling interface and state reduction optimizations     cannot allocate memory for the page tables.
together has the most significant effect on the search space     3) uKernel userspace: The generated code cannot access the
size, because it effectively reduces the size of the grammar     registers or in-memory data structures directly, instead, in-
with which we generate programs. Moreover, optimizing            voking operations through system calls. It performs the re-
the possible set of expressions further reduces the search       quired memory allocations for the translation descriptors.
space significantly. The tree-based structure does not reduce       We chose Barrelfish, a capability-based uKernel, as ca-
the maximum number of candidate programs, but instead,           pability operations provide a nice separation of tasks for
quickly eliminates programs that do not satisfy the goal.        managing page tables. We add a mmap-like system call to the
Discussion. This evaluation shows that domain-specific op-       kernel to test the monolithic scenario. For all three cases,
timization techniques reduce the search space significantly,     we replace the existing code with the generated code. We
making the synthesis process tractable for modern machines.      boot the system on x86_64 Qemu with KVM acceleration
                                                                 such that the hardware performs the page table walk where
6.4   Hardware/Software Co-Design with Velosiraptor              the guest page tables are set up by Velosiraptor-generated
We demonstrate Velosiraptor’s ability to generate transla-       code. We then perform a sequence of memory mappings and
tion hardware components and the corresponding code that         accesses to the mapped regions to test whether the memory
configures it from the same description, using a qualitative     hardware has been configured correctly.
study targeting the Arm Fast Models platform simulator.          Results and Discussion. We observed that the generated
Methodology. We generate an emulated hardware com-               code correctly programs the translation hardware, the sys-
ponent for the Arm Fast Models and instantiate it in the         tem booted, and ran the tests successfully. The OS environ-
platform description file by placing it between the main sys-    ment specification can adapt the code generation of Velosir-
tem bus and a DRAM region. Memory accesses to a distinct,        aptor to handle a diverse set of environments.
contiguous memory address range on the system bus will
be forwarded to the generated translation hardware compo-        6.6   Performance of Generated Code
nent. The hardware component maps or rejects the memory          We evaluate the performance of the generated code by com-
accesses based on the behavioral description and its current     paring the runtime performance against hand-written code
state. In case of a translation fault, a synchronous exception   of other operating systems.
is raised to enable integration with the OS as with MMU-         Methodology. We run the evaluation entirely in userspace
based translation faults. Velosiraptor generates the hardware    on Linux to avoid the overheads of system calls and rule
ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands          Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


                 Operation       Map     Protect Unmap              the translation tables. Velosiraptor can handle generating the
       Structure   Code      P50 P95 P50 P95 P50 P95
                                                                    code for both the system call or capability invocations and
         x86_64    Linux     13ns 13ns 13ns 13ns 12ns 12ns
         x86_64 Velosiraptor 13ns 13ns 12ns 12ns 11ns 12ns          the kernel’s updating of translation table entries (Section 6.5).
         PTable   Barrelfish 8ns 8ns 8ns 9ns 7ns 8ns                Device Driver Synthesis. Termite [59, 60] synthesizes de-
         PTable Velosiraptor 8ns 8ns 8ns 8ns 8ns 8ns                vice drivers using a game-theoretic approach. It expresses
Table 3. Performance comparison of Velosiraptor-generated           what happens when the OS interacts with device registers
code with hand-written code from Linux and Barrelfish.              (e.g., the character sent event), whereas Velosiraptor focuses
                                                                    on the resulting mapping, independent of the register inter-
                                                                    actions. Termite has no support for in-memory data struc-
                                                                    tures and cannot generate corresponding hardware. Ghost-
out possible differences in the OS environment. The page-
                                                                    Writer [66] uses behavior trees to synthesize device drivers
table structures are allocated on the heap. We extract the
                                                                    by specifying the corresponding device behavior but it nei-
hand-written x86_64 page table code from the Barrelfish
                                                                    ther generates hardware nor expresses mapping behavior.
OS and the Linux kernel v6.8 and compare it against the
                                                                    Porting. Porting an OS to new platforms requires significant
Velosiraptor-generated code. We measure the latency of the
                                                                    effort [54]. Chen et al. [18] show a signification reduction
addmap, setperms, and delmap over 200 iterations.
                                                                    in developer time by generating 70% of device driver code
Results and Discussion. Table 3 shows the median and
                                                                    utilizing domain-specific aspects such as device classes and
95th percentile latencies of the three functions. The x86_64
                                                                    features. Velosiraptor follows a similar approach by synthe-
structure sets up the full four-level page table structure in
                                                                    sizing the memory management code. Hu et al. [32] present a
memory, whereas PTable only configures the leaf level of the
                                                                    system for automated porting of an OS to new platforms us-
page table. We observe that there is no significant difference
                                                                    ing a machine-independent OS specification and a machine-
between Velosiraptor and the hand-written code.
                                                                    dependent language describing the instruction set. Their
                                                                    work targets assembly code resulting in a huge search space,
6.7   Discussion
                                                                    whereas Velosiraptor operates on a higher-level abstraction,
We demonstrated that Velosiraptor produces performant code          i.e., API requests with a more manageable search space.
that configures the memory hardware in a wide range of              Hardware Description. Describing the hardware interface
settings Potential barriers to integrating the Velosiraptor-        using a specification language allows for the generation of
generated code into a larger OS are replacing existing, pos-        OS bindings. For example, the Mackerel language [58] and
sibly tightly integrated data structures, e.g., Linux’s paging      Ghostwriter’s register definition file [66] are domain-specific
data types being passed around in the kernel instead of using       languages for describing registers and data structures used
high-level functions. The OS may make use of non-present            by devices. Neither includes the hardware behavior so can-
translation table entries to store information on swapped-out       not generate the hardware itself. The Arm architecture is
pages, or during NUMA-balancing operations. The high-level          specified in ASL [55] that serves as the basis for generating
functions generated by Velosiraptor do not expose functional-       the documentation, instruction interpreters [57], simulators
ity for these use cases, but the enumeration construct could        for processors, and test suites for chip designers [56].
be used to express OS-specific use cases (e.g., swap entries).      MMU Virtualization. Several works virtualize the MMU
                                                                    to provide isolation of system components and to enforce
7     Related Work                                                  security policies through intercepting and restricting ac-
MMU Configurations. Achermann et al. [1] present a                  cess to the MMU configuration to validate configuration
toolchain for automatically generating a static initial page        updates. Para-virtualization used in Xen [13] and Linux’s
table for x86 and Arm-based systems based on a formal de-           PV-Ops interface [65] intercepts updates to the page tables.
scription of the memory topology [3, 4]. Their work focused         SecPod [67] isolates page-table management through pag-
on calculating the right address mappings to install into the       ing delegation and execution trapping to enforce auditing
page table. Fiedler et al. [27, 28] define trust boundaries based   the kernel’s page-table modifications by leveraging the PV-
on the accessibility of control registers and translation ta-       Ops interface. SecVisor [61] virtualizes the MMU by control-
bles. Dörr et al. [26] focus on access permissions and the          ling all modifications to the page tables using nested paging
generation of static configurations. In contrast, Velosiraptor      and enforces policies on the execute permissions. Hypervi-
provides functions to dynamically change the configura-             sion [11] validates page table updates in the secure monitor.
tion of memory hardware at runtime and supports memory              Nested kernel [24] separates the kernel into a trusted, nested
hardware besides translation tables. Memory hardware man-           kernel that has control over the MMU, and an untrusted outer
agement can also be split between user-space and kernel.            kernel that has no direct control over the MMU. Similarly,
For example, Barrelfish [16], seL4 [39] and mmapx [2], allow        Nexen [62] uses the nested kernel architecture to introduce
userspace to safely manage translation tables by separating         a secure monitor into Xen by enforcing read-only page ta-
the construction from writing the actual bit patterns into          bles. SVA [22] prevents the OS from mapping frames used
Velosiraptor : Code Synthesis for Memory Translation                        ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands


by the ghost memory partition or SVA VM internal memory          by assigning types to pages and then using this type informa-
as ordinary memory. Inktag [31] divides physical memory          tion when constructing page tables (similar to the typed capa-
into secure and non-secure frames where secure frames can        bilities in seL4 [39] and Barrelfish [16]). Velosiraptor defines
only be mapped by the trusted extended page table in a           a type per page table node to ensure correct construction.
nested paging setup. Overshadow [19] protects applications       Moreover, through OS specification the generated code can
from the OS by leveraging context-dependent one-to-many          be tailored to API functions (e.g., sva.update.lN.mapping)
mappings through the use of multiple shadow page tables.         or the corresponding handler code in the kernel. seKVM [42]
Mondrix [69] overlays the address space with protection          provides a model and a verified implementation for the
domains assigning permissions to specific memory regions.        ARMv8 virtual memory system, including a proof that the
   Enforcing the security policies is orthogonal to Velosirap-   resulting data structure is indeed a tree – a property that
tor. Those systems could use Velosiraptor-generated code in      follows by construction from Velosiraptor’s specification lan-
the “bottom half” of the virtualized MMU, i.e., the trusted      guage. Moreover, seKVM has layers for allocation, walking,
component that directly interacts with the physical MMU.         and constructing the page table, similar to the generated func-
Moreover, by tailoring the generated code with the OS spec-      tions of Velosiraptor. However, seKVM targets the ARMv8
ification, Velosiraptor can provide the corresponding para-      architecture whereas Velosiraptor allows generating the cor-
virtualized interface that intercepts page table updates and     responding functions for any given specification. Li et al. [43]
invokes the trusted component instead – similar to the ap-       verified a concurrent implementation of multi-level realm
proach taken with Barrelfish in Section 6.5.                     translation tables for the Arm architecture using their VIA
Hardware Mechanisms. Several systems use hardware                framework. The proof is tied to the Arm architecture and
extensions to enforce isolation and protection. Hardware-        leverages the CertiKOS [30] methodology. CertiKOS itself
assisted kernel compartmentalization (HAKCs) [47] parti-         uses a two-level page map that follows the x86_32 page table
tions the code and data of a monolithic kernel and defines       structure. Velosiraptor could be used to generate code for
access policy for each partition using Arm’s PAC [7] and         other page tables and the corresponding proofs in the VIA
MTE [8] extensions. xMP [53] uses Intel’s VMFunc [37] to         framework. HyperKernel [52] ensures ownership properties
quickly switch the extended page tables to accelerate pro-       of the root-level page table to ensure safety and security
tection domain switching. vTZ [33] virtualizes Arm’s secure      guarantees. With Velosiraptor, porting Hyperkernel to other
world before hardware support has been introduced [44]           architectures could be simplified by generating the code that
by leveraging the secure/non-secure modes and restricting        configures the page tables. Dai et al. [23] verified the sec-
second-stage translation configuration to the secure world.      ond stage translation setup of HyperEnclave, focusing on a
HDFI [64] and CHERI [68] use tag-based memory protec-            framework to verify the correctness using a deep embedding
tion to perform an additional, hardware-accelerated permis-      of Rust’s MIR in Coq. Brun et al. [17] and Lattuada et al. [41]
sion check on every load/store instruction. ACES [20] uses a     verify the correctness of a Rust implementation of the x86_64
compiler-based approach to compartmentalize and isolate          page table in Verus with focus on hardware concurrency, an
components through binary instrumentation and uses mem-          aspect which we plan to integrate in the future.
ory protection units to enforce access control. SKEE [12]
creates an isolated environment by disallowing the kernel        8   Conclusion
from managing its own translation tables, and forcing up-        Correctly configuring the memory hardware of a platform is
dates through a well-defined switch gate. EC [38] uses a         of paramount importance for the system integrity. Hardware
𝜇Kernel-design to isolate components using a memory pro-         is becoming more diverse and complex, and OS developers
tection unit and hardware watchpoints to monitor its config-     must adapt their code to the hardware they run on – a manual
uration. Kenali [63] maintains a shadow address space with       process that takes time and requires developers to deal with
different access permissions and enforces MMU integrity by       subtle, low-level hardware details.
restricting access to the MMU-related data and registers.           Velosiraptor is a methodology and system that uses soft-
   Leveraging hardware features such as Intel’s VMFfunc,         ware synthesis to automatically and efficiently generate cor-
memory tagging or watchpoints, or maintaining multiple           rect implementations for addmap, setperms, and delmap to
page tables and shadow mappings is orthogonal to Velosirap-      change the mapping behavior of memory hardware. Velosir-
tor. However, the Velosiraptor-generated code could be used      aptor lets developers generate the corresponding memory
to set up the MMU-based address translation, MPU-based           hardware itself, enabling research into new mapping schemes
memory protection, or create fat-pointers (e.g., CHERI [68]).    that precisely have the features the developer wants.
We leave encryption-based approaches, e.g., pointer signa-
tures, as future work.                                           Acknowledgments
Formal Modeling and Verification. KCoFI [21] provides an         This work was supported by the Natural Sciences and Engi-
interface to safely manage the page tables for an SVA VM [22]    neering Research Council of Canada (NSERC).
ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands       Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


A     Artifact                                                   conditions. Arm-based machines are not tested and only
A.1    Abstract                                                  support a subset of the experiments and are thus not recom-
                                                                 mended. If a virtual machine is used, please ensure an x86_64
The artifact consists of
                                                                 host and appropriate configuration of hardware acceleration
 • the Velosiraptor toolchain,                                   (e.g., KVM) when running the performance benchmarks.
 • a set of mapping specifications,
 • a set of benchmarks / tests to reproduce the results in the   A.3.3 Software dependencies. The artifact is tested on
    paper, and                                                   x86_64 Ubuntu 24.04 server – other operating systems, e.g.,
 • and a modified version of the Barrelfish OS that uses the     other Linux distributions and Windows Subsystem for Linux,
    Velosiraptor-generated code.                                 may work too, but are not tested. The README.md file pro-
The following contains dependencies and instructions to          vides a detailed list of software packages and other software
reproduce the results presented in the evaluation Section 6      dependencies that can be installed using Ubuntu’s package
of the paper.                                                    manager. Additional dependencies are: Rust 1.79, Z3 4.10.2,
                                                                 Docker, and Arm Fast Models 11.15.
A.2    Artifact check-list (meta-information)
                                                                 A.4    Installation and Basic Test
 • Algorithm: Yes.
 • Compilation: Rust 1.79 and GCC 13.2.0                         Follow the instructions in the Preparation section of the
 • Binary: requires Z3 SMT Solver, Arm FastModels, and           README.md file in the repository to setup the build and
   Qemu                                                          run environment of the artifact. Beyond the dependencies,
 • Run-time environment: Linux (Ubuntu 24.04)                    there is no installation necessary and the artifact builds and
 • Hardware: x86_64 machine with a minimum of 8 cores            runs out of the repository.
   and 32GB of RAM, either baremetal or a virtual machine          Basic Test: To test the artifact run the smoke test from
 • Run-time state: clean OS installation.                        section 6.2 and/or run the test Section 6.3. This exercises
 • Execution: cargo / bash scripts.
                                                                 the synthesis workflow, SMT solver, optimizations, and code
 • Metrics: quantitative: performance (latency). Qualitative:
                                                                 compilation.
   functionality.
 • Output: Latex tables 1, 2, and 3, code and OS logs.
                                                                 A.5    Experiment workflow
 • Experiments: a total of five experiments each correspond-
   ing to a subsection in Section 6.                             Most of the experiments are run through cargo commands
 • How much disk space required?: 10GB.                          or bash scripts as described in the README.md file of the
 • How much time is needed to prepare workflow?: One             artifact repository. The workflow consists of two phases:
   hour.
                                                                     1. running the respective commands to execute the ex-
 • How much time is needed to complete experiments?: Six
   hours.                                                               periment, and
 • Publicly available?: Yes, https://github.com/ubc-systopia/        2. inspecting the output to verify and compare the results.
   velosiraptor-asplos25-artifact                                The README.md contains detailed descriptions of the com-
 • Code licenses?: MIT.                                          mands and the expected output.
 • Data licenses?: None.
 • Workflow automation framework used?: No.                      A.6    Evaluation and expected results
 • Archived (provide DOI)?: 10.5281/zenodo.14752297 or on
   GitHub repository.                                            The artifact is expected to
                                                                     1. closely reproduce Tables 1, 2, and 3 in the evaluation
A.3    Description                                                      Section 6 of the paper (quantitative benchmarks), and
A.3.1 How to access. Clone the git repository at https://            2. emit similar output as described in the README.md
github.com/ubc-systopia/velosiraptor-asplos25-artifact and              file for the remaining experiments of Sections 6.4 and
follow the instructions in the README.md file. Alternatively,           6.5 in the paper (qualitative benchmarks).
download the artifact from DOI: 10.5281/zenodo.14752297
                                                                 A.7    Experiment customization
Ensure to initialize the submodules recursively. The respos-
itory contains all the code and data sets, and instructions      Most experiments run within a few minutes in the current
to install dependencies that are required to reproduce the       configuration. For the longer-running synthesis experiment
results on the machine.                                          (Table 1), we provide a smoke test that runs a smaller ver-
                                                                 sion of the experiment. Moreover, experiments can also be
A.3.2 Hardware dependencies. The artifact requires one           customized by changing the set of specifications that are
x86_64 machine (either baremetal or a virtual machine) with      evaluated, or the number of iterations executed. This re-
at least eight cores and 32GB of RAM. Smaller machines may       quires modifying the respective benchmarking code in the
also work, but can lead to longer runtimes or out-of-memory      repository.
Velosiraptor : Code Synthesis for Memory Translation                                        ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands


A.8    Notes                                                                         (CCS ’14). Association for Computing Machinery, New York, NY, USA,
                                                                                     90–102. doi:10.1145/2660267.2660350
   Arm Fast Models Licenses. The emulated hardware plat-                        [12] Ahmed M. Azab, Kirk Swidowski, Rohan Bhutkar, Jia Ma, Wenbo
forms require the Arm Fast Models to build and run the                               Shen, Ruowen Wang, and Peng Ning. 2016. SKEE: A lightweight
simulators. The Arm Fast Models require licenses. To down-                           Secure Kernel-level Execution Environment for ARM. In Network and
load the Arm Fast Models and and obtaining the correspond-                           Distributed System Security Symposium (San Diego, California, USA)
ing licenses, visit the Arm website: https://www.arm.com/                            (NDSS’16). The Internet Society. doi:10.14722/ndss.2016.23009
                                                                                [13] Paul Barham, Boris Dragovic, Keir Fraser, Steven Hand, Tim Harris,
products/development-tools/simulation/fast-models. The
                                                                                     Alex Ho, Rolf Neugebauer, Ian Pratt, and Andrew Warfield. 2003. Xen
artifact assumes that the user has access to                                         and the art of virtualization. In Proceedings of the Nineteenth ACM
    1. the Arm Fast Models and its third-party IP,                                   Symposium on Operating Systems Principles (Bolton Landing, NY, USA)
    2. license for generating the simulation platform,                               (SOSP ’03). Association for Computing Machinery, New York, NY, USA,
                                                                                     164–177. doi:10.1145/945445.945462
    3. license to run the base platform, and                                    [14] Clark Barrett, Pascal Fontaine, and Cesare Tinelli. 2021. The SMT-LIB
    4. license to run the Arm Cortex A57 processor IP.                               Standard. https://smt-lib.org/papers/smt-lib-reference-v2.6-r2021-05-
                                                                                     12.pdf Version 2.6.
References                                                                      [15] Arkaprava Basu, Jayneel Gandhi, Jichuan Chang, Mark D. Hill, and
 [1] Reto Achermann, David Cock, Roni Haecki, Nora Hossle, Lukas Hum-                Michael M. Swift. 2013. Efficient virtual memory for big memory
     bel, Timothy Roscoe, and Daniel Schwyn. 2021. Generating Correct                servers. SIGARCH Comput. Archit. News 41, 3 (jun 2013), 237–248.
     Initial Page Tables from Formal Hardware Descriptions. In Proceedings           doi:10.1145/2508148.2485943
     of the 11th Workshop on Programming Languages and Operating Systems        [16] Andrew Baumann, Paul Barham, Pierre-Evariste Dagand, Tim Harris,
     (Virtual Event, Germany, 2021) (PLOS ’21). Association for Computing            Rebecca Isaacs, Simon Peter, Timothy Roscoe, Adrian Schüpbach, and
     Machinery, New York, NY, USA, 69–75. doi:10.1145/3477113.3487270                Akhilesh Singhania. 2009. The multikernel: a new OS architecture for
 [2] Reto Achermann, David Cock, Roni Haecki, Nora Hossle, Lukas Hum-                scalable multicore systems. In Proceedings of the ACM SIGOPS 22nd
     bel, Timothy Roscoe, and Daniel Schwyn. 2021. mmapx: uniform                    Symposium on Operating Systems Principles (Big Sky, Montana, USA)
     memory protection in a heterogeneous world. In Proceedings of the               (SOSP ’09). Association for Computing Machinery, New York, NY, USA,
     Workshop on Hot Topics in Operating Systems (Ann Arbor, Michigan,               29–44. doi:10.1145/1629575.1629579
     2021) (HotOS ’21). Association for Computing Machinery, New York,          [17] Matthias Brun, Reto Achermann, Tej Chajed, Jon Howell, Gerd Zell-
     NY, USA, 159–166. doi:10.1145/3458336.3465273                                   weger, and Andrea Lattuada. 2023. Beyond isolation: OS verification
 [3] Reto Achermann, Lukas Humbel, David Cock, and Timothy Roscoe.                   as a foundation for correct applications. In Proceedings of the 19th
     2017. Formalizing Memory Accesses and Interrupts. In Proceedings                Workshop on Hot Topics in Operating Systems (Providence, Rhode Is-
     2nd Workshop on Models for Formal Analysis of Real Systems, MARS                land, USA) (HotOS’23). Association for Computing Machinery, 158–165.
     at ETAPS 2017, Uppsala, Sweden, 29th April 2017. (2017) (MARS’17).              doi:10.1145/3593856.3595899
     66–116. doi:10.4204/EPTCS.244.4                                            [18] H. Chen, G. Godet-Bar, F. Rousseau, and F. Petrot. 2014. Device driver
 [4] Reto Achermann, Lukas Humbel, David Cock, and Timothy Roscoe.                   generation targeting multiple operating systems using a model-driven
     2018. Physical Addressing on Real Hardware in Isabelle/HOL. In                  methodology. In 2014 25nd IEEE International Symposium on Rapid
     Proceedings of the 9th International Conference on Interactive Theorem          System Prototyping. 30–36. doi:10.1109/RSP.2014.6966689
     Proving, 2018, Held as Part of the Federated Logic Conference, FloC 2018   [19] Xiaoxin Chen, Tal Garfinkel, E. Christopher Lewis, Pratap Subrah-
     (Oxford, UK, 2018) (ITP’18). 1–19. doi:10.1007/978-3-319-94821-8_1              manyam, Carl A. Waldspurger, Dan Boneh, Jeffrey Dwoskin, and
 [5] Reto Achermann, Ilias Karimalis, and Margo Seltzer. 2023. Why write             Dan R.K. Ports. 2008. Overshadow: a virtualization-based approach to
     address translation OS code yourself when you can synthesize it?. In            retrofitting protection in commodity operating systems. In Proceed-
     Proceedings of the 19th Workshop on Hot Topics in Operating Systems             ings of the 13th International Conference on Architectural Support for
     (Providence, RI, USA) (HOTOS ’23). Association for Computing Ma-                Programming Languages and Operating Systems (Seattle, WA, USA)
     chinery, New York, NY, USA, 174–180. doi:10.1145/3593856.3595895                (ASPLOS XIII). Association for Computing Machinery, New York, NY,
 [6] Hanna Alam, Tianhao Zhang, Mattan Erez, and Yoav Etsion. 2017.                  USA, 2–13. doi:10.1145/1346281.1346284
     Do-It-Yourself Virtual Memory Translation. In Proceedings of the 44th      [20] Abraham A. Clements, Naif Saleh Almakhdhub, Saurabh Bagchi, and
     Annual International Symposium on Computer Architecture (Toronto,               Mathias Payer. 2018. ACES: automatic compartments for embedded
     ON, Canada) (ISCA ’17). Association for Computing Machinery, New                systems. In Proceedings of the 27th USENIX Conference on Security
     York, NY, USA, 457–468. doi:10.1145/3079856.3080209                             Symposium (Baltimore, MD, USA) (SEC’18). USENIX Association, USA,
 [7] Arm Ltd. 2016.           Introduction to PAC.            Online. https:         65–82.
     //developer.arm.com/documentation/109576/0100/Pointer-                     [21] John Criswell, Nathan Dautenhahn, and Vikram Adve. 2014. KCoFI:
     Authentication-Code/Introduction-to-PAC.                                        Complete Control-Flow Integrity for Commodity Operating System
 [8] Arm Ltd. 2019. Armv8.5-A – Memory Tagging Extension. White                      Kernels. In Proceedings of the 2014 IEEE Symposium on Security and
     Paper.                                                                          Privacy (SP ’14). IEEE Computer Society, USA, 292–307. doi:10.1109/
 [9] Arm Ltd. 2023. LISA+ Language for Fast Models Reference Manual.                 SP.2014.26
     https://developer.arm.com/documentation/101092/0100 Version 1.0..          [22] John Criswell, Andrew Lenharth, Dinakar Dhurjati, and Vikram Adve.
[10] Arm Ltd. 2024. Fast Models: SoC Verification Without Hardware. On-              2007. Secure virtual architecture: a safe execution environment for
     line. https://www.arm.com/products/development-tools/simulation/                commodity operating systems. In Proceedings of Twenty-First ACM
     fast-models.                                                                    SIGOPS Symposium on Operating Systems Principles (Stevenson, Wash-
[11] Ahmed M. Azab, Peng Ning, Jitesh Shah, Quan Chen, Rohan Bhutkar,                ington, USA) (SOSP ’07). Association for Computing Machinery, New
     Guruprasad Ganesh, Jia Ma, and Wenbo Shen. 2014. Hypervision                    York, NY, USA, 351–366. doi:10.1145/1294261.1294295
     Across Worlds: Real-time Kernel Protection from the ARM TrustZone          [23] Zhenyang Dai, Shuang Liu, Vilhelm Sjoberg, Xupeng Li, Yu Chen, Wen-
     Secure World. In Proceedings of the 2014 ACM SIGSAC Conference on               hao Wang, Yuekai Jia, Sean Noble Anderson, Laila Elbeheiry, Shubham
     Computer and Communications Security (Scottsdale, Arizona, USA)                 Sondhi, Yu Zhang, Zhaozhong Ni, Shoumeng Yan, Ronghui Gu, and
                                                                                     Zhengyu He. 2024. Verifying Rust Implementation of Page Tables in a
ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands                       Reto Achermann, Em Chu, Ryan Mehri, Ilias Karimalis, and Margo Seltzer


     Software Enclave Hypervisor. In Proceedings of the 29th ACM Interna-        [34] Jian Huang, Moinuddin K. Qureshi, and Karsten Schwan. 2016. An Evo-
     tional Conference on Architectural Support for Programming Languages             lutionary Study of Linux Memory Management for Fun and Profit. In
     and Operating Systems, Volume 2 (La Jolla, CA, USA) (ASPLOS ’24).                Proceedings of the 2016 USENIX Conference on Usenix Annual Technical
     Association for Computing Machinery, New York, NY, USA, 1218–1232.               Conference (Denver, CO, USA) (USENIX ATC ’16). USENIX Associa-
     doi:10.1145/3620665.3640398                                                      tion, Berkeley, CA, USA, 465–478. http://dl.acm.org/citation.cfm?id=
[24] Nathan Dautenhahn, Theodoros Kasampalis, Will Dietz, John Criswell,              3026959.3027002
     and Vikram Adve. 2015. Nested Kernel: An Operating System Ar-               [35] Integrated Device Technology, Inc. 1995. IDT79R4600 TM and
     chitecture for Intra-Kernel Privilege Separation. In Proceedings of the          IDT79R4700 TM RISC Processor Hardware User’s Manual (revision 2.0
     Twentieth International Conference on Architectural Support for Pro-             ed.). https://docslib.org/doc/718203/idt79r4600-and-idt79r4700-risc-
     gramming Languages and Operating Systems (Istanbul, Turkey) (ASP-                processor-hardware-users-manual
     LOS ’15). Association for Computing Machinery, New York, NY, USA,           [36] Intel Corp. 2013. Intel Xeon Phi Coprocessor Developer’s Quick Start
     191–206. doi:10.1145/2694344.2694386                                             Guide.     https://www.intel.com/content/dam/develop/external/us/
[25] Leonardo De Moura and Nikolaj Bjørner. 2008. Z3: an efficient SMT                en/documents/intel-xeon-phi-coprocessor-quick-start-developers-
     solver. In Proceedings of the Theory and Practice of Software, 14th In-          guide.pdf Version 1.8.
     ternational Conference on Tools and Algorithms for the Construction         [37] Intel Corp. 2023. Intel 64 and IA-32 Architectures Software Devel-
     and Analysis of Systems (Budapest, Hungary) (TACAS’08/ETAPS’08).                 oper’s Manual. https://www.intel.com/content/www/us/en/developer/
     Springer-Verlag, Berlin, Heidelberg, 337–340.                                    articles/technical/intel-sdm.html December 2023.
[26] Tobias Dörr, Timo Sandmann, and Jürgen Becker. 2021. Model-based            [38] Arslan Khan, Dongyan Xu, and Dave Jing Tian. 2023. EC: Em-
     configuration of access protection units for multicore processors in             bedded Systems Compartmentalization via Intra-Kernel Isolation.
     embedded systems. Microprocess. Microsyst. 87, C (nov 2021), 17 pages.           In 2023 IEEE Symposium on Security and Privacy (SP). 2990–3007.
     doi:10.1016/j.micpro.2021.104377                                                 doi:10.1109/SP46215.2023.10179285
[27] Ben Fiedler, Roman Meier, Jasmin Schult, Daniel Schwyn, and Timothy         [39] Gerwin Klein, Kevin Elphinstone, Gernot Heiser, June Andronick,
     Roscoe. 2023. Specifying the de-facto OS of a production SoC. In Pro-            David Cock, Philip Derrin, Dhammika Elkaduwe, Kai Engelhardt, Rafal
     ceedings of the 1st Workshop on Kernel Isolation, Safety and Verification        Kolanski, Michael Norrish, Thomas Sewell, Harvey Tuch, and Simon
     (Koblenz, Germany) (KISV ’23). Association for Computing Machinery,              Winwood. 2009. seL4: formal verification of an OS kernel. In Proceed-
     New York, NY, USA, 18–25. doi:10.1145/3625275.3625400                            ings of the ACM SIGOPS 22nd Symposium on Operating Systems Princi-
[28] Ben Fiedler, Daniel Schwyn, Constantin Gierczak-Galle, David Cock,               ples (Big Sky, Montana, USA) (SOSP ’09). Association for Computing
     and Timothy Roscoe. 2023. Putting out the hardware dumpster fire.                Machinery, New York, NY, USA, 207–220. doi:10.1145/1629575.1629596
     In Proceedings of the 19th Workshop on Hot Topics in Operating Sys-         [40] Joshua Landgraf, Matthew Giordano, Esther Yoon, and Christopher J.
     tems (Providence, RI, USA) (HOTOS ’23). Association for Computing                Rossbach. 2023. Reconfigurable Virtual Memory for FPGA-Driven I/O.
     Machinery, New York, NY, USA, 46–52. doi:10.1145/3593856.3595903                 In Proceedings of the 28th ACM International Conference on Architectural
[29] Krishnan Gosakan, Jaehyun Han, William Kuszmaul, Ibrahim N.                      Support for Programming Languages and Operating Systems, Volume 3
     Mubarek, Nirjhar Mukherjee, Karthik Sriram, Guido Tagliavini, Evan               (Vancouver, BC, Canada) (ASPLOS 2023). Association for Computing
     West, Michael A. Bender, Abhishek Bhattacharjee, Alex Conway, Mar-               Machinery, New York, NY, USA, 556–571. doi:10.1145/3582016.3582048
     tin Farach-Colton, Jayneel Gandhi, Rob Johnson, Sudarsun Kannan,            [41] Andrea Lattuada, Travis Hance, Jay Bosamiya, Matthias Brun, Chanhee
     and Donald E. Porter. 2023. Mosaic Pages: Big TLB Reach with                     Cho, Hayley LeBlanc, Pranav Srinivasan, Reto Achermann, Tej Chajed,
     Small Pages. In Proceedings of the 28th ACM International Confer-                Chris Hawblitzel, Jon Howell, Jacob R. Lorch, Oded Padon, and Bryan
     ence on Architectural Support for Programming Languages and Op-                  Parno. 2024. Verus: A Practical Foundation for Systems Verification. In
     erating Systems, Volume 3 (Vancouver, BC, Canada) (ASPLOS 2023).                 Proceedings of the ACM SIGOPS 30th Symposium on Operating Systems
     Association for Computing Machinery, New York, NY, USA, 433–448.                 Principles (Austin, TX, USA) (SOSP ’24). Association for Computing
     doi:10.1145/3582016.3582021                                                      Machinery, New York, NY, USA, 438–454. doi:10.1145/3694715.3695952
[30] Ronghui Gu, Zhong Shao, Hao Chen, Xiongnan (Newman) Wu, Jie-                [42] Shih-Wei Li, Xupeng Li, Ronghui Gu, Jason Nieh, and John Zhuang
     ung Kim, Vilhelm Sjöberg, and David Costanzo. 2016. CertiKOS: An                 Hui. 2021. Formally Verified Memory Protection for a Commodity Mul-
     Extensible Architecture for Building Certified Concurrent OS Ker-                tiprocessor Hypervisor. In 30th USENIX Security Symposium (USENIX
     nels. In 12th USENIX Symposium on Operating Systems Design and                   Security 21). USENIX Association, 3953–3970. https://www.usenix.
     Implementation (OSDI 16). USENIX Association, Savannah, GA, 653–                 org/conference/usenixsecurity21/presentation/li-shih-wei
     669. https://www.usenix.org/conference/osdi16/technical-sessions/           [43] Xupeng Li, Xuheng Li, Christoffer Dall, Ronghui Gu, Jason Nieh,
     presentation/gu                                                                  Yousuf Sait, and Gareth Stockwell. 2022. Design and Verification
[31] Owen S. Hofmann, Sangman Kim, Alan M. Dunn, Michael Z. Lee,                      of the Arm Confidential Compute Architecture. In 16th USENIX Sym-
     and Emmett Witchel. 2013. InkTag: secure applications on an un-                  posium on Operating Systems Design and Implementation (OSDI 22).
     trusted operating system. In Proceedings of the Eighteenth Interna-              USENIX Association, Carlsbad, CA, 465–484. https://www.usenix.org/
     tional Conference on Architectural Support for Programming Languages             conference/osdi22/presentation/li
     and Operating Systems (Houston, Texas, USA) (ASPLOS ’13). Asso-             [44] Berenice Mann. 2018.           New Secure world architecture in
     ciation for Computing Machinery, New York, NY, USA, 265–278.                     Armv8.4. Online. https://community.arm.com/arm-community-
     doi:10.1145/2451116.2451146                                                      blogs/b/architectures-and-processors-blog/posts/architecting-more-
[32] Jingmei Hu, Eric Lu, David A. Holland, Ming Kawaguchi, Stephen                   secure-world-with-isolation-and-virtualization.
     Chong, and Margo Seltzer. 2023. Towards Porting Operating Systems           [45] A Theodore Markettos, Colin Rothwell, Brett F Gutstein, Allison
     with Program Synthesis. ACM Trans. Program. Lang. Syst. 45, 1, Article           Pearce, Peter G Neumann, Simon W Moore, and Robert NM Wat-
     2 (mar 2023), 70 pages. doi:10.1145/3563943                                      son. 2019. Thunderclap: Exploring Vulnerabilities in Operating Sys-
[33] Zhichao Hua, Jinyu Gu, Yubin Xia, Haibo Chen, Binyu Zang, and                    tem IOMMU Protection via DMA from Untrustworthy Peripherals. In
     Haibing Guan. 2017. vTZ: Virtualizing ARM TrustZone. In 26th                     NDSS.
     USENIX Security Symposium (USENIX Security 17). USENIX Associa-             [46] Alex Markuze, Adam Morrison, and Dan Tsafrir. 2016. True IOMMU
     tion, Vancouver, BC, 541–556. https://www.usenix.org/conference/                 Protection from DMA Attacks: When Copy is Faster Than Zero Copy.
     usenixsecurity17/technical-sessions/presentation/hua                             In Proceedings of the Twenty-First International Conference on Archi-
                                                                                      tectural Support for Programming Languages and Operating Systems
Velosiraptor : Code Synthesis for Memory Translation                                     ASPLOS ’25, March 30-April 3, 2025, Rotterdam, Netherlands


     (Atlanta, Georgia, USA) (ASPLOS ’16). ACM, New York, NY, USA, 249–           doi:10.1145/1629575.1629583
     262. doi:10.1145/2872362.2872379                                        [60] Leonid Ryzhyk, Adam Walker, John Keys, Alexander Legg, Arun
[47] Derrick McKee, Yianni Giannaris, Carolina Ortega, Howard Shrobe,             Raghunath, Michael Stumm, and Mona Vij. 2014. User-Guided Device
     Mathias Payer, Hamed Okhravi, and Nathan Burow. 2022. Preventing             Driver Synthesis. In Proceedings of the 11th USENIX Conference on Op-
     Kernel Hacks with HAKCs. In 29th Annual Network and Distributed              erating Systems Design and Implementation (Broomfield, CO) (OSDI’14).
     System Security Symposium (San Diego, California, USA) (NDSS’22).            USENIX Association, USA, 661–676.
     The Internet Society. doi:10.14722/ndss.2022.24026                      [61] Arvind Seshadri, Mark Luk, Ning Qu, and Adrian Perrig. 2007. SecVi-
[48] Benot Morgan, Eric Alata, Vincent Nicomette, and Mohamed Kaaniche.           sor: a tiny hypervisor to provide lifetime kernel code integrity for
     2016. Bypassing IOMMU Protection against I/O Attacks. In 2016 Sev-           commodity OSes. In Proceedings of Twenty-First ACM SIGOPS Sympo-
     enth Latin-American Symposium on Dependable Computing (LADC).                sium on Operating Systems Principles (Stevenson, Washington, USA)
     145–150. doi:10.1109/LADC.2016.31                                            (SOSP ’07). Association for Computing Machinery, New York, NY, USA,
[49] Benot Morgan, Eric Alata, Vincent Nicomette, and Mohamed Kaaniche.           335–350. doi:10.1145/1294261.1294294
     2018. IOMMU Protection Against I/O Attacks: A Vulnerability and a       [62] Lei Shi, Yuming Wu, Yubin Xia, Nathan Dautenhahn, Haibo Chen,
     Proof of Concept. Journal of the Brazilian Computer Society 24, 1 (09        Binyu Zang, Haibing Guan, and Jinming Li. 2017. Deconstructing Xen.
     Jan 2018), 2. doi:10.1186/s13173-017-0066-7                                  In Proceedings 2017 Network and Distributed System Security Symposium
[50] National Vulnerability Database. 2014. CVE-2014-9888. Online.https:          (NDSS’17). Internet Society. doi:10.14722/ndss.2017.23455
     //nvd.nist.gov/vuln/detail/CVE-2014-9888.                               [63] Chengyu Song, Byoungyoung Lee, Kangjie Lu, William Harris, Taesoo
[51] National Vulnerability Database. 2017. CVE-2017-16994. Online. https:        Kim, and Wenke Lee. 2016. Enforcing Kernel Security Invariants
     //nvd.nist.gov/vuln/detail/CVE-2017-16994.                                   with Data Flow Integrity. In 23rd Annual Network and Distributed
[52] Luke Nelson, Helgi Sigurbjarnarson, Kaiyuan Zhang, Dylan Johnson,            System Security Symposium (San Diego, California, USA) (NDSS’16).
     James Bornholt, Emina Torlak, and Xi Wang. 2017. Hyperkernel: Push-          The Internet Society. doi:10.14722/ndss.2016.23218
     Button Verification of an OS Kernel. In Proceedings of the 26th Sym-    [64] Chengyu Song, Hyungon Moon, Monjur Alam, Insu Yun, Byoungy-
     posium on Operating Systems Principles (Shanghai, China) (SOSP ’17).         oung Lee, Taesoo Kim, Wenke Lee, and Yunheung Paek. 2016. HDFI:
     Association for Computing Machinery, New York, NY, USA, 252–269.             Hardware-Assisted Data-Flow Isolation. In 2016 IEEE Symposium on
     doi:10.1145/3132747.3132748                                                  Security and Privacy (SP’16). 1–17. doi:10.1109/SP.2016.9
[53] Sergej Proskurin, Marius Momeu, Seyedhamed Ghavamnia, Vasileios P.      [65] The kernel development community. 2024. Paravirt_ops. The Linux
     Kemerlis, and Michalis Polychronakis. 2020. xMP: Selective Memory            Kernel Organization. https://www.kernel.org/doc/html/latest/virt/
     Protection for Kernel and User Space. In 2020 IEEE Symposium on              paravirt_ops.html
     Security and Privacy (SP). 563–577. doi:10.1109/SP40000.2020.00041      [66] Bingyao Wang, Sepehr Noorafshan, Reto Achermann, and Margo
[54] Richard Rashid, Avadis Tevanian, Michael Young, David Golub, Robert          Seltzer. 2023. Synthesizing Device Drivers with Ghost Writer. In Pro-
     Baron, David Black, William Bolosky, and Jonathan Chew. 1987.                ceedings of the 12th Workshop on Programming Languages and Operat-
     Machine-independent virtual memory management for paged unipro-              ing Systems (Koblenz, Germany) (PLOS ’23). Association for Computing
     cessor and multiprocessor architectures. In Proceedings of the Second        Machinery, New York, NY, USA, 10–17. doi:10.1145/3623759.3624545
     International Conference on Architectual Support for Programming Lan-   [67] Xiaoguang Wang, Yue Chen, Zhi Wang, Yong Qi, and Yajin Zhou. 2015.
     guages and Operating Systems (Palo Alto, California, USA) (ASPLOS            SecPod: a framework for virtualization-based security systems. In
     II). Association for Computing Machinery, New York, NY, USA, 31–39.          Proceedings of the 2015 USENIX Conference on Usenix Annual Technical
     doi:10.1145/36206.36181                                                      Conference (Santa Clara, CA) (USENIX ATC ’15). USENIX Association,
[55] Alastair Reid. 2016. ARM’s Architecture Specification Language. On-          USA, 347–360.
     line. https://alastairreid.github.io/specification_languages/.          [68] Robert N. M. Watson, Jonathan Woodruff, Peter G. Neumann, Si-
[56] Alastair Reid. 2016. Trustworthy Specifications of ARM v8-A and v8-M         mon W. Moore, Jonathan Anderson, David Chisnall, Nirav Dave,
     System Level Architecture. In Proceedings of the 16th Conference on          Brooks Davis, Khilan Gudka, Ben Laurie, Steven J. Murdoch, Robert
     Formal Methods in Computer-Aided Design (Mountain View, California)          Norton, Michael Roe, Stacey Son, and Munraj Vadera. 2015. CHERI:
     (FMCAD ’16). FMCAD Inc, Austin, Texas, 161–168.                              A Hybrid Capability-System Architecture for Scalable Software Com-
[57] Alastair Reid. 2020. Using ASLi with Arm’s v8.6-A ISA specification.         partmentalization. In Proceedings of the 2015 IEEE Symposium on
     Online. https://alastairreid.github.io/using-asli/.                          Security and Privacy (SP ’15). IEEE Computer Society, USA, 20–37.
[58] Timothy Roscoe and Barrelfish Projec. [n. d.]. Mackerel User Guide –         doi:10.1109/SP.2015.9
     Barrelfish Technical Note 2.                                            [69] Emmett Witchel, Junghwan Rhee, and Krste Asanović. 2005. Mon-
[59] Leonid Ryzhyk, Peter Chubb, Ihor Kuz, Etienne Le Sueur, and Ger-             drix: memory isolation for linux using mondriaan memory protec-
     not Heiser. 2009. Automatic Device Driver Synthesis with Ter-                tion. In Proceedings of the Twentieth ACM Symposium on Operat-
     mite. In Proceedings of the ACM SIGOPS 22nd Symposium on Op-                 ing Systems Principles (Brighton, United Kingdom) (SOSP ’05). As-
     erating Systems Principles (Big Sky, Montana, USA) (SOSP ’09). As-           sociation for Computing Machinery, New York, NY, USA, 31–44.
     sociation for Computing Machinery, New York, NY, USA, 73–86.                 doi:10.1145/1095810.1095814
