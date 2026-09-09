import unittest
from position_bridge import calculate

class Check(unittest.TestCase):
    def test_rectangular_image_coordinates(self):
        r=calculate([dict(kind='text',tokens=2),dict(kind='image',preprocessed_height=64,preprocessed_width=96),dict(kind='text',tokens=1)],3)
        self.assertEqual(r['positions'],[[0,1,2,2,2,2,2,2,5],[0,1,2,2,2,3,3,3,5],[0,1,2,3,4,2,3,4,5]])
        self.assertEqual(r['summary']['rope_delta'],-3)
        self.assertEqual(r['summary']['decode_rotary_positions'],[6,7])
        self.assertEqual(r['summary']['final_kv_positions'],11)
    def test_book_geometry(self):
        segments=[]
        for _ in range(4):segments.extend([dict(kind='text',tokens=100),dict(kind='image',preprocessed_height=640,preprocessed_width=640)])
        s=calculate(segments,128)['summary']
        self.assertEqual((s['prompt_positions'],s['image_positions'],s['rope_delta'],s['next_rotary_position']),(2000,1600,-1520,480))
        self.assertEqual(s['final_kv_positions'],2127)
    def test_text_only(self):
        s=calculate([dict(kind='text',tokens=17)],2)['summary']
        self.assertEqual(s['rope_delta'],0)
        self.assertEqual(s['decode_rotary_positions'],[17])
    def test_invalid(self):
        for seg in [[],[dict(kind='text',tokens=True)],[dict(kind='image',preprocessed_height=33,preprocessed_width=64)],[dict(kind='text',tokens=1),dict(kind='text',tokens=2)]]:
            with self.assertRaises(ValueError):calculate(seg)
    def test_count_independent_coordinates(self):
        for h in range(1,5):
            for w in range(1,5):
                r=calculate([dict(kind='text',tokens=3),dict(kind='image',preprocessed_height=h*32,preprocessed_width=w*32)])
                self.assertEqual(r['summary']['rope_delta'],max(h,w)-h*w)
                for j in range(h*w):
                    self.assertEqual([a[j+3] for a in r['positions']],[3,3+j//w,3+j%w])

if __name__=='__main__':unittest.main()
