/* Own dependency-free late-load probe. No constructors or product effects. */
__attribute__((visibility("default"), noinline, noclone))
int frw_fixture_solib_probe(void) { return 0x46525731; }
