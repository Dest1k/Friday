This is a SOURCE-ONLY delta to the frozen accepted Source100 three-module composition. It supports only the existing exact `en_US.UTF-8` branch and the newly proven exact selected `LC_ALL=C.UTF-8` branch. Root retains its actual `LANG=LC_ALL=C.UTF-8` launch. No locale/config/font alteration is needed or authorized by this package.

For the C.UTF-8 branch the actual loaded Root record must retain all existing Source100 facts and additionally contain:

```json
{
  "startup_locale_environment": {"LC_ALL": "C.UTF-8"},
  "lifecycle": {
    "exclusive_owner_operation_id": "<actual operation id>",
    "profile_origin": "CREATED_EMPTY_FOR_THIS_OPERATION",
    "application_settings": "STARTUP_CONFIG_UNMODIFIED",
    "reference_operations": ["LOAD_CALC_WORKING_COPY"],
    "stock_locale_initialization": "DESKTOP_PREPARE_LOCALE_COMPLETED_NO_LATER_LANGUAGE_MUTATION"
  }
}
```

`startup_locale_environment` is the selected effective LC_ALL input, not the whole execve environment. Root's separate actual launch evidence retains the complete cleared/allowlisted environment, including `LANG=C.UTF-8`. The Linux i18n path selects the nonempty LC_ALL before LC_CTYPE/LANG; the resolver never reads its own process environment and never guesses missing fields. Additional keys in this selected-input dictionary refuse. Unsupported LC_ALL values and actual nonempty config other than exact `en-US` refuse.

The new token is a Root lifecycle fact, not a direct native getter, a result of `ooSetupSystemLocale`, or a fabricated config-provided native-language proof. Root may bind it when all of the following are true:

1. Root owns a freshly execve-launched exact pinned stock standalone soffice.bin PID/birth and the sole private empty profile/endpoint. It has verified the actual source/component linkage and launch environment. This is neither an attached prior Office nor LOK/fuzzing nor a custom embedding path. Root knows there was no other caller, programmatic acceptor enabling or native-language override.
2. Root has successfully connected through that actual process's normal enabled remote Office acceptor and obtained its remote context/Desktop, then loaded the one admitted private working copy with the existing abort-only/read-only/no-macros/no-links/no-network/no-restore load contract. Local PyUNO bootstrap, a bootstrap context, the existence of a socket/profile/config object, or a launcher returning successfully cannot establish this.
3. The pinned startup control flow is applicable: Desktop::Init calls prepareLocale; failure marks bootstrap error. Main rejects bootstrap errors before posting EnableAcceptors. Stock acceptors begin disabled; their worker waits for enable before accepting a connection/creating the remote bridge. A genuine same-process normal remote bridge under the exclusive launch facts therefore establishes passage through successful stock locale initialization. The safe load gives the real Calc model used by Source100; it does not itself invent the startup fact.
4. Root's exclusive lifecycle preserves the same startup configuration view and selected environment. No native/system/Application language mutation, configuration reload/override, arbitrary automation, macro/script/extension, extra document/client, LOK language selection, or alternate component/settings writer has intervened. The qualifier reads actual `ooSetupSystemLocale` and checks it again after metric Font restoration. It cannot detect a native settings mutation that bypasses config; Root must establish the controlled history.

Incompatible later actions include `LanguageTag::setConfiguredSystemLanguage`, the underlying configured-language setter, `Application::SetSettings`/`AllSettings::SetLanguageTag` changing locale, LOK locale/language APIs, a change to `/org.openoffice.Setup/L10N/ooSetupSystemLocale`, registry/config replacement/reload, or execution of an unreviewed caller capable of such changes. UI `ooLocale`, source text `CharLocale`, and SAL's process `rtl_Locale` are not substitutes for Application locale. The accepted read-only API inspection, admitted safe single Calc load, and R2's finally-restored temporary Font operations preserve the already accepted Source100 model; they grant no general mutation right.

Native derivation is exact and narrow: Linux i18n inunx reads LC_ALL, isolang splits `C.UTF-8` to language `C` and empty country, lowercases it, and maps the exact `c` other-name to LANGUAGE_ENGLISH_US. No generic fallback or host libc locale availability is needed. prepareLocale uses that platform language if actual system-locale config is empty, or exact actual config `en-US` otherwise; makeFallback and the configured setter establish the same known en-US native branch. SysLocale/AllSettings and the accepted English-US-to-LATIN script chain then apply under the controlled lifecycle. SAL's Unix `osl_getProcessLocale` uses a distinct parser (`C.`/empty/`UTF-8` for C.UTF-8); Linux inunx does not call it. No SAL query was performed or is required to prove this source branch.

The qualifier passes `stock_startup_locale_lifecycle=<exact token>` to both pre- and postquery calls of the resolver only on selected C.UTF-8. The resolver keyword defaults to None for the old path. The C default-script leaf evidence uses the existing `ROOT_EXTERNAL_RECORD` basis and the independently bound loaded-record digest. Font observation metadata separately labels the token `EXTERNAL_ROOT_INPUT_NOT_API_OBSERVED`; the returned script remains `SOURCE_DERIVED_STARTUP_APPLICATION_STATE`. The top loaded-record schema string remains v1 with one conditional C-only lifecycle field. Existing en-US calls omit that field and keyword. Callbacks, R2 leaf schema/signature, raw32 mode, native64 postquery join, Font restore, no-M/no-runtime-acceptance outputs are unchanged.

Sol101 integration dependency: use this exact qualifier and resolver afterimage together with the unchanged Source100 R2. Supply the new lifecycle field only for exact selected C.UTF-8 and retain the corresponding actual Root runner evidence reference in the already existing loaded record. Recompute exact code/record pins. Do not fill the token from a config value or from fixture truth. If Root cannot establish these lifecycle premises, stop before metric queries with C_UTF8_stock_startup_language_lifecycle_UNBOUND; a bounded future native language observation would be a separately owned Root operation, never a source PASS in this package.

This package performs no Office/UNO/SAL/native/font probe, load/model/render/send/install/service/config action. It proves neither actual M nor physical units, current runtime qualification, historical applicability, nor formal/product acceptance.
