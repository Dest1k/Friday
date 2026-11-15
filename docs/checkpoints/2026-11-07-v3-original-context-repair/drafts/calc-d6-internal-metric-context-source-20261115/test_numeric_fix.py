"""Finite fixes for independent review R1/R2; all metric values synthetic."""
from pathlib import Path
from decimal import Decimal,localcontext
from fractions import Fraction
from dataclasses import replace
import hashlib,importlib.util,unittest
from test_d6_context import ROOT,SOURCE,DEST,c,r,m,mutate,synthetic_context


class NumericFix(unittest.TestCase):
    def test_near_half_source_and_full_generated_consumer_refuse(self):
        raw='2.0644999999999999999999cm'
        value=Fraction(Decimal(raw[:-2]))
        with self.assertRaisesRegex(m.MetricContextError,'xml_length_binary_rounding_unassessed'):
            m.lo_262_export_mm100(value,original_length=raw)
        def change(root):
            for node in root.iter(r.q(r.ST,'style')):
                if node.get(r.q(r.ST,'name'))=='co1':
                    node.find(r.q(r.ST,'table-column-properties')).set(r.q(r.ST,'column-width'),raw)
        data=mutate(SOURCE,'content.xml',change)
        source=c.inventory(data,'ods')
        self.assertEqual(source.destination_profile,m.PROFILE)
        # Recreate the independently found BAD algorithm token in a separate
        # synthetic target, solely to show the new full consumer refuses it.
        p=ROOT/'reviewed-initial/tools/scoped_spreadsheet_calc_metric.py'
        spec=importlib.util.spec_from_file_location('initial_numeric_model',p)
        old=importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name]=old;spec.loader.exec_module(old)
        widths={}
        for row in source.rich_signature.native_geometry:
            if row[0]!='column_width':continue
            feature,name,first,last,length=row
            token=old.lo_262_explicit_export_token(old.lo_262_export_mm100(Fraction(*length)),raw_m=126)
            for column in range(first,last+1):widths[name,column]=token
        target=DEST
        for index,(name,cells) in enumerate(source.sheets,1):
            def tokens(root):
                cols=root.find(r.q(r.S,'cols'))
                for col in (() if cols is None else cols):
                    values={widths[name,i] for i in range(int(col.get('min')),int(col.get('max'))+1)}
                    self.assertEqual(len(values),1);col.set('width',str(values.pop()))
            target=mutate(target,f'xl/worksheets/sheet{index}.xml',tokens)
        context=replace(synthetic_context(data,target),raw_m=126)
        with self.assertRaisesRegex(c.ConversionRefused,'xml_length_binary_rounding_unassessed'):
            c.validate_destination(source,target,'xlsx',_calc_metric_context=context)
    def test_original_lexemes_required_bound_to_rational_and_exact_coverage(self):
        for raw in ('1cm','10mm','0.3937007874015748031496062992in','28.34645669291338582677165354pt'):
            # Only exact rational equivalence may assert a given rational cm.
            if raw in ('1cm','10mm'):
                self.assertEqual(m.lo_262_export_mm100(Fraction(1),original_length=raw),1000)
            else:
                with self.assertRaisesRegex(m.MetricContextError,'geometry_mismatch'):
                    m.lo_262_export_mm100(Fraction(1),original_length=raw)
        with self.assertRaisesRegex(m.MetricContextError,'lexeme_required'):
            m.lo_262_export_mm100(Fraction(1),original_length=None)
    def test_decimal_precision_does_not_change_explicit_token(self):
        for precision in (1,2,3,28,100):
            with self.subTest(precision=precision),localcontext() as ctx:
                ctx.prec=precision
                self.assertEqual(m.lo_262_explicit_export_token(3113,raw_m=126),Decimal('14.01'))
    def test_retained_three_lengths_avoid_new_xml_refusal_and_match_source98(self):
        source=c.inventory(SOURCE,'ods')
        lengths={key[-1] for key in source.rich_signature.native_geometry if key[0]=='column_width'}
        self.assertEqual(len(lengths),3)
        lexemes={(name,i):raw for name,first,last,raw in source.rich_signature._calc_column_lengths for i in range(first,last+1)}
        for row in source.rich_signature.native_geometry:
            if row[0]!='column_width':continue
            feature,name,first,last,length=row
            exact=Fraction(*length);value=exact*1000
            # Source98 positive exact half-up integer normalization.
            half=lambda f:(2*f.numerator+f.denominator)//(2*f.denominator)
            expected=half(Fraction(half(Fraction(half(value)*72,127))*127,72))
            self.assertEqual(m.lo_262_export_mm100(exact,original_length=lexemes[name,first]),expected)

if __name__=='__main__':unittest.main(verbosity=2)
