"""Pure synthetic algorithm/plumbing controls. No actual metric or case PASS."""
from pathlib import Path
from dataclasses import replace,fields
from decimal import Decimal
from fractions import Fraction
from unittest.mock import patch
from types import ModuleType
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as E
import copy,hashlib,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'candidate'))
from tools import scoped_spreadsheet_rich as r,scoped_spreadsheet_conversion as c
from tools import scoped_spreadsheet_calc_metric as m
from test_generated_profile import SOURCE,DEST,mutate,rawmutate,cell


def sha(data):return hashlib.sha256(data).hexdigest()


def synthetic_context(source,destination):
    """Invented facts, deliberate synthetic M128; never a runtime witness."""
    fake=sha(b'SYNTHETIC FACT ONLY - NOT OBSERVED OR QUALIFIED')
    return m.CalcReferenceMetricContext(
        sha(source),len(source),sha(destination),len(destination),'26.2.5.2',
        m.REVIEWED_COMMIT,m.RULE,fake,tuple((k,fake) for k in m.COMPONENT_ROLES),
        'Default',('Calibri',Decimal(11)),'LATIN','Calibri',0,220,
        fake,fake,fake,fake,128)


def synthetic_destination(source):
    # Do not inspect target tokens to select M. M128 is an invented fixed test
    # scalar. Rewrite only a separate in-memory synthetic target's tokens.
    widths={}
    lexemes={(name,col):raw for name,first,last,raw in source.rich_signature._calc_column_lengths for col in range(first,last+1)}
    for row in source.rich_signature.native_geometry:
        if row[0]!='column_width':continue
        _,name,first,last,length=row
        token=m.lo_262_explicit_export_token(m.lo_262_export_mm100(Fraction(*length),original_length=lexemes[name,first]),raw_m=128)
        for col in range(first,last+1):widths[name,col]=token
    current=DEST
    for index,(name,cells) in enumerate(source.sheets,1):
        def rewrite(root):
            cols=root.find(r.q(r.S,'cols'))
            if cols is not None:
                for node in cols:
                    tokens={widths[name,i] for i in range(int(node.get('min')),int(node.get('max'))+1)}
                    assert len(tokens)==1
                    node.set('width',str(tokens.pop()))
        current=mutate(current,f'xl/worksheets/sheet{index}.xml',rewrite)
    assert sha(current)!=sha(DEST),'synthetic target must never be named b93'
    return current


class ContextControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=c.inventory(SOURCE,'ods')
        cls.synthetic=synthetic_destination(cls.source)
        cls.context=synthetic_context(SOURCE,cls.synthetic)
    def validate(self,data=None,context=None):
        return c.validate_destination(self.source,self.synthetic if data is None else data,'xlsx',
                _calc_metric_context=self.context if context is None else context)
    def test_actual_immutable_pair_UNBOUND_still_refuses_all_consumers(self):
        for ctx in (None,{},replace(self.context,source_sha256='0'*64)):
            with self.subTest(context=type(ctx).__name__):
                with self.assertRaises(c.ConversionRefused):
                    c.validate_destination(self.source,DEST,'xlsx',_calc_metric_context=ctx)
        projected,sig=c._prepare_rich(DEST,'xlsx',None,self.source)
        actual=c._with_rich(c._scalar_inventory(projected,'xlsx',None,False,sig),sig,'xlsx')
        for consumer in (r.compare_rich,r.declared_losses,r.fidelity_report):
            with self.assertRaises(r.ODSError):consumer(self.source.rich_signature,actual.rich_signature)
    def test_synthetic_full_validate_and_fidelity_use_same_context(self):
        actual=self.validate()
        self.assertEqual(self.source.sheets,actual.sheets)
        report=r.fidelity_report(self.source.rich_signature,actual.rich_signature,_calc_metric_context=self.context)
        self.assertIn('column_width_physical_mapping_unassessed',report['unassessed'])
        self.assertIn('physical_geometry_quantized_0.001cm',report['declared_losses'])
        # Metadata retains BOTH original maps; target tokens aren't overwritten.
        source=[d for d in report['dimension_metadata'] if d['feature']=='column_width' and d['side']=='source']
        target=[d for d in report['dimension_metadata'] if d['feature']=='column_width' and d['side']=='destination']
        self.assertTrue(source and target)
        self.assertEqual(source[0]['unit'],'cm_rational')
        self.assertEqual(target[0]['unit'],'xlsx_character_width')
        self.assertNotEqual(source[0]['data'],target[0]['data'])
        for consumer in (r.compare_rich,r.declared_losses,r.fidelity_report):
            with self.assertRaises(r.ODSError):consumer(self.source.rich_signature,actual.rich_signature)
    def test_synthetic_context_shape_rule_bytes_and_metric_negatives(self):
        bad={'source_sha256':'0'*64,'destination_sha256':'0'*64,'source_bytes':0,
             'destination_bytes':True,'producer_version':'26.2.5.3','reviewed_source_commit':'0'*40,
             'numeric_rule':'unknown','recipe_sha256':None,'component_sha256':(),
             'source_style_name':'Other','source_font':('Arial',Decimal(11)),
             'default_script':'CJK','export_name':'','export_charset':True,
             'raw_font_height':221,'font_descriptor_sha256':None,'font_view_sha256':None,
             'reference_state_sha256':None,'applicability_sha256':None,'raw_m':None}
        for field,value in bad.items():
            with self.subTest(field=field):
                with self.assertRaises(c.ConversionRefused):self.validate(context=replace(self.context,**{field:value}))
        for value in (False,0,-1,65536,Decimal(128),127):
            with self.subTest(raw_m=value):
                with self.assertRaises(c.ConversionRefused):self.validate(context=replace(self.context,raw_m=value))
        with self.assertRaises(c.ConversionRefused):self.validate(context=self.context.__dict__)
    def test_neighboring_original_token_cannot_be_hidden_by_projection(self):
        changed=mutate(self.synthetic,'xl/worksheets/sheet1.xml',lambda root:root.find(r.q(r.S,'cols'))[0].set('width',str(Decimal(root.find(r.q(r.S,'cols'))[0].get('width'))+Decimal('.01'))))
        # Rebind synthetic destination identity so the numeric guard must run.
        ctx=replace(self.context,destination_sha256=sha(changed),destination_bytes=len(changed))
        with self.assertRaisesRegex(c.ConversionRefused,'calc_exact_producer_token_mismatch'):self.validate(changed,ctx)
    def test_full_column_xml_domain_overlap_and_coverage(self):
        mutations=[lambda cols:cols.remove(cols[0]),
                   lambda cols:cols.append(copy.deepcopy(cols[0])),
                   lambda cols:cols[0].set('min','0'),
                   lambda cols:cols[0].set('max','65'),
                   lambda cols:cols[0].set('width','0'),
                   lambda cols:cols[0].set('width','256')]
        for change in mutations:
            data=mutate(self.synthetic,'xl/worksheets/sheet1.xml',lambda root:change(root.find(r.q(r.S,'cols'))))
            ctx=replace(self.context,destination_sha256=sha(data),destination_bytes=len(data))
            with self.subTest(change=mutations.index(change)):
                with self.assertRaises(c.ConversionRefused):self.validate(data,ctx)
    def test_raw_geometry_must_have_exact_coverage_domain_and_no_overlap(self):
        actual=self.validate();source=self.source.rich_signature
        originals=actual.rich_signature.native_geometry
        rows=[row for row in originals if row[0]=='column_width'];first=rows[0]
        for geometry in (tuple(row for row in originals if row!=first),originals+(first,),
                         originals+(('column_width','OTHER',1,1,Decimal(1)),),
                         tuple((row[:2]+(0,)+row[3:]) if row==first else row for row in originals),
                         tuple((row[:-1]+(Decimal('NaN'),)) if row==first else row for row in originals)):
            altered=copy.copy(actual.rich_signature);altered.__dict__.update(actual.rich_signature.__dict__);altered.native_geometry=geometry
            with self.subTest(geometry_count=len(geometry)):
                with self.assertRaises(r.ODSError):r.compare_rich(source,altered,_calc_metric_context=self.context)
    def test_sheets_hidden_modes_and_source_profile_stay_strict(self):
        actual=self.validate();source=self.source.rich_signature
        for attr,value in [('sheet_names',('OTHER',)),('_destination_profile',''),('native_calc_profile',False)]:
            altered=copy.copy(source);altered.__dict__.update(source.__dict__);setattr(altered,attr,value)
            with self.subTest(attr=attr):
                with self.assertRaises(r.ODSError):r.compare_rich(altered,actual.rich_signature,_calc_metric_context=self.context)
        hidden=next(row for row in source if row[0]=='hidden_row')
        for records in (tuple(row for row in source if row!=hidden),tuple(row for row in source if row[0]!='native_hidden_mode')):
            altered=r.RichSignature(records);altered.__dict__.update(source.__dict__)
            with self.assertRaises(r.ODSError):r.compare_rich(altered,actual.rich_signature,_calc_metric_context=self.context)
    def test_same_format_raw_geometry_and_ordinary_paths_do_not_use_context(self):
        left=r.RichSignature([('column_width','S',(1,1,Decimal('1.000')))])
        right=r.RichSignature(left)
        for sig in (left,right):sig.source_kind='xlsx';sig.sheet_names=('S',)
        left.native_geometry=(('column_width','S',1,1,Decimal('8.71')),)
        right.native_geometry=(('column_width','S',1,1,Decimal('8.71001')),)
        with self.assertRaisesRegex(r.ODSError,'native_geometry_mismatch'):
            r.compare_rich(left,right,_calc_metric_context=self.context)
        self.assertTrue(r.compare_rich(left,left,_calc_metric_context={}))
        ordinary=r.RichSignature([('column_width','S',(1,1,Decimal('1.001')))])
        ordinary.source_kind='ods'
        with self.assertRaisesRegex(r.ODSError,'semantic_mismatch'):
            r.compare_rich(left,ordinary,_calc_metric_context=self.context)
    def test_source98_arithmetic_and_explicit_unproved_edges(self):
        self.assertEqual(m.lo_262_export_mm100(Fraction(1),original_length='1cm'),1000)
        self.assertEqual(m.lo_262_explicit_export_token(1000,raw_m=128),Decimal('4.43'))
        for length in (Fraction(1,2000),Fraction(0),Fraction(1001),Fraction(120)):
            with self.subTest(length=length):
                with self.assertRaises(m.MetricContextError):m.lo_262_export_mm100(length,original_length=str(float(length))+'cm')
        # Pure arithmetic input 127/144000 gives exact .5 centicharacter.
        with self.assertRaisesRegex(m.MetricContextError,'binary_half_boundary'):
            m.lo_262_explicit_export_token(127,raw_m=14400)
    def test_nearest_render_internal_plumbing_synthetic_NO_OFFICE(self):
        from hermes_cli import friday_workspace_spreadsheet_conversion as caller
        pdf=ModuleType('hermes_cli.friday_workspace_pdf')
        pdf._toolchain=lambda:ROOT/'synthetic-toolchain-does-not-exist'
        pdf._run=lambda *args:None
        pdf.ExportRefused=RuntimeError
        revision=ModuleType('hermes_cli.friday_workspace_revision');revision.check=lambda cap:None
        original_mkdtemp=tempfile.mkdtemp
        def own_temp(*args,**kwargs):return original_mkdtemp(prefix='synthetic-render-',dir=ROOT)
        with patch.dict(sys.modules,{'hermes_cli.friday_workspace_pdf':pdf,'hermes_cli.friday_workspace_revision':revision}),patch.object(caller,'_argv',return_value=['SYNTHETIC-NO-EXECUTION']),patch.object(caller,'_read_output',return_value=self.synthetic),patch.object(caller.tempfile,'mkdtemp',side_effect=own_temp):
            rendered,meta=caller.render(object(),SOURCE,'ods','xlsx',_calc_metric_context=self.context)
            self.assertEqual(rendered,self.synthetic)
            self.assertFalse(meta['rich_spreadsheet_profile_preserved'])
            self.assertFalse(meta['runtime_qualified'])
            self.assertIn('column_width_physical_mapping_unassessed',meta['fidelity']['unassessed'])
            with self.assertRaises(c.ConversionRefused):caller.render(object(),SOURCE,'ods','xlsx')

if __name__=='__main__':unittest.main(verbosity=2)
