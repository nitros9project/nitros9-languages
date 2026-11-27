import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('rma_library', Path(__file__).parents[1]/'rma-library.py')
rma = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rma)


class RmaLibraryTests(unittest.TestCase):
    def test_stack_checker_uses_the_compiler_startup_alias(self):
        result=rma.convert(' extern _stkcheck\n section code\n lbsr _stkcheck\n endsection\n','stack')
        self.assertIn(' lbsr _stkchec\n',result)


    def test_macro_calls_keep_the_renamed_definition(self):
        result=rma.convert(' section code\nnegd macro\n nega\n negb\n sbca #0\n endm\n negd\n endsection\n','macro')
        import re
        name=re.search(r'^(\w+) macro$',result,re.M)[1]
        self.assertIn(' '+name+'\n',result)
        self.assertNotIn(' negd\n',result)

    def test_direct_page_reservations_remain_direct_page(self):
        result=rma.convert(' section directpage\ncount: rmb 1\n endsection\n','dp')
        self.assertIn(' vsect dp\n',result)

    def test_byte_complement_is_truncated_to_the_operand_width(self):
        result=rma.convert(' section code\nmask equ ^$80\n lda #mask\n endsection\n','byte')
        self.assertIn(' lda #127\n',result)


    def test_initialized_pointer_image_becomes_relocatable_vsect(self):
        text = ''' export table
 extern target
 section data
unit.img.0:
unit.il.0.0:
 fdb target
unit.end.0:
 section bss
unit.bss.0: rmb unit.end.0-unit.img.0
table equ unit.bss.0+(unit.il.0.0-unit.img.0)
 section irec
 fdb unit.img.0
 fdb unit.end.0
 fdb unit.bss.0
 section ireloc
 fdb unit.bss.0
 section code
 endsection
'''
        result = rma.convert(text, 'l001')
        self.assertRegex(result, r'table:\n(?:\w+\n)* fdb target')
        self.assertNotIn(' rmb ', result)
        self.assertEqual(result.count(' fdb '), 1)
        self.assertIn(' vsect', result)
        self.assertNotIn('ireloc', result)

    def test_absolute_bit_expressions_do_not_reach_old_rma(self):
        result = rma.convert(' section code\na equ $01\nb equ $04\nmask equ a|b\n bitb #mask\n andb #^(a|b)\n endsection\n', 'l002')
        self.assertIn(' bitb #5', result)
        self.assertIn(' andb #250', result)
        self.assertNotIn('|', result)

    def test_long_external_spelling_matches_provider(self):
        provider = rma.convert(' section code\nlong_function EXPORT\nlong_function: rts\n endsection\n', 'l003')
        client = rma.convert(' section code\nlong_function EXTERNAL\n lbsr long_function\n endsection\n', 'l004')
        symbol = client.split(' lbsr ')[1].splitlines()[0]
        self.assertLessEqual(len(symbol), 8)
        self.assertIn(symbol+': rts', provider)

    def test_rma_comments_and_character_literals(self):
        result = rma.convert(' section code\n ldb #\' \'\ttrailing comment\n fcc /a;b/ ; comment\n endsection\n', 'l005')
        self.assertIn(' ldb #32', result)
        self.assertIn(' fcb 97,59,98', result)
        self.assertNotIn('trailing comment', result)

    def test_library_scans_cover_backwards_chains_and_cycles(self):
        units = [({'c'}, {'d'}), ({'b'}, {'c'}), ({'a'}, {'b'}), ({'d'}, {'a'})]
        self.assertEqual(rma.library_scans(units), 4)

    def test_unknown_section_fails_instead_of_losing_data(self):
        with self.assertRaises(ValueError):
            rma.convert(' section unsupported\n rmb 8\n', 'l006')


if __name__ == '__main__':
    unittest.main()
