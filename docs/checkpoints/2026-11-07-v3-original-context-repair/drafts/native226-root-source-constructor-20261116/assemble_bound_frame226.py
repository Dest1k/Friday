"""Root's finite SOURCE-only entry; explicit pinned refs, no current/effects.

This reads the named Root binding config and exact addressed immutable CODE/data
refs. It never follows input credential/TLS/runtime/userpayload references.
Only complete source-constructor success can create a new own cache frame.
"""
from pathlib import Path
import argparse,dataclasses,hashlib,importlib.util,json,os,sys
os.umask(0o077)
sys.dont_write_bytecode=True
B=Path(__file__).parent

def load_module():
    spec=importlib.util.spec_from_file_location('Root226FiniteConstructor',B/'construct_frame226.py')
    value=importlib.util.module_from_spec(spec);sys.modules[spec.name]=value;spec.loader.exec_module(value);return value

def assemble(m, config):
    m.require(type(config)is dict and config.get('schema')=='frw.Root226.explicit-source-binding-inputs.v1' and config.get('source_only')is True and config.get('current_admission')is False and config.get('execution_grant')is False,'explicit_Root_SOURCE226_binding_config_required')
    # Validate future Product and Origin refs before any plan/boundary/metadata
    # access. Only the already loaded config has been read at this boundary.
    fixed_config=config.get('fixed')
    origin_ref=fixed_config.get('public_origin') if type(fixed_config)is dict else None
    m.future_product_origin_ref_checked(config.get('product_source_commit'),origin_ref)
    origin=m.SuppliedBytes(origin_ref,m.refraw(origin_ref))
    m.future_product_origin_checked(config['product_source_commit'],origin)
    p=config['plan'];plan=m.prepare_source_plan(**{f:p[f]for f in ('before','after','project_roots','previous_project_roots','native_rows','external_callers','source_metadata')})
    acceptance=m.RootSourceAcceptance(**config['acceptance']);m.acceptance_checked(plan,acceptance)
    boundary=m.boundary_module(plan)
    envelopes={}
    for flavor in ('private','public'):
        value=config['base_envelopes'][flavor]
        envelopes[flavor]=m.RootEnvelopeInput(m.refraw(value['source_ref']),boundary.RootEnvelopeProjection(**value['projection']))
    inputs=m.RootSourceInputs(acceptance,**envelopes)
    fixed={k:(origin if k=='public_origin' else m.SuppliedBytes(r,m.refraw(r)))for k,r in config['fixed'].items()}
    binding=json.loads(m.refraw(config['actual225_binding']))
    actual={k:m.SuppliedBytes(dict(path=binding[k]['cache_path'],sha256=binding[k]['sha256'],bytes=binding[k]['bytes']),m.refraw(dict(path=binding[k]['cache_path'],sha256=binding[k]['sha256'],bytes=binding[k]['bytes'])))for k in m.ROLES}
    sources={name:m.refraw(r)for name,r in config['frame_sources'].items()}
    native={k:m.SuppliedBytes(r,m.refraw(r))for k,r in config['native_after'].items()}
    additional={r['path']:m.refraw(r)for r in config['additional_source_refs']}
    data=m.RootFrameData(inputs,config['frame'],config['product_source_commit'],fixed,binding,actual,native,sources,additional,config['budgets'],config['python'],config['provenance'])
    return m.render_bound_frame(plan,data)

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root-inputs',required=True);a.add_argument('--sha256',required=True);a.add_argument('--write',action='store_true',help='Create only new constructor-validated own SOURCE cache frame; no current or execution')
    args=a.parse_args();m=load_module();config=json.loads(m.refraw(dict(path=args.root_inputs,sha256=args.sha256)));result=assemble(m,config)
    frame=m.cache_path(config['frame'])
    m.require(frame.parent==B.parent and frame.name.startswith('bound-source-frame226-'),'own226_output_only')
    if args.write:
        frame.mkdir(mode=0o700)
        for name,raw in result['output_bytes'].items():
            path=frame/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    print(json.dumps(dict(schema='frw.Root226.finite-source-constructor-result.v1',state='BOUND_SOURCE_BYTES_WRITTEN'if args.write else 'VIRTUAL_SOURCE_CONSTRUCTOR_JOINED',source_only=True,current_admission=False,execution_grant=False,maintenance_started=False,actual_fullinput_consumer_accepted=False,frame=str(frame),files=len(result['output_bytes']),source_pins_sha256=m.sha(result['output_bytes']['SOURCE-PINS.json']),projection=result['projection'])))
if __name__=='__main__':main()
