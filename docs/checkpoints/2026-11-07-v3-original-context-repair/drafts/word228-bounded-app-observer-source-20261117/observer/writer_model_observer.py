"""Getter-only observation of one *already supplied* Writer document.

This module imports no UNO provider and performs no loading, navigation, saving,
filesystem/network/process access, registration, or capability/authority action.
It supplies observations, never App custody, provenance, or acceptance evidence.

API SUPPORT BOUNDARY: Root must qualify effective ``PageStyleName`` semantics on
the model-only cursor created at each BODY paragraph start in its real Writer.
The guarded property query below is deliberately the sole discovery route.
Property availability alone does not establish that semantic qualification.
There is no PageDescName, view-controller, arbitrary style, or default fallback.
Root must also qualify the queried page-style properties on the actual provider.
"""

SCHEMA = "word228.loaded-writer-observation.v1"
ROLE = "observation_only_no_app_custody_or_acceptance"
BODY_PARAGRAPHS = 5
MAX_STORY_PARAGRAPHS = 16
MAX_PORTIONS_PER_PARAGRAPH = 256
MAX_TOTAL_CODEPOINTS = 131072
MAX_URL_CODEPOINTS = 4096
MAX_STYLE_NAME_CODEPOINTS = 256


class AppObservationUnsupported(Exception):
    """The exact, guarded model API is unavailable; no substitution is valid."""

    def __init__(self, reason, stage, api):
        self.reason = reason
        self.stage = stage
        self.api = api


class AppObservationRefused(Exception):
    """The supplied model has a shape outside this bounded observation slice."""

    def __init__(self, reason, stage, api=""):
        self.reason = reason
        self.stage = stage
        self.api = api


def _call(obj, method, stage, *args):
    try:
        fn = getattr(obj, method)
    except Exception:
        raise AppObservationUnsupported("model_method_unavailable", stage, method) from None
    if not callable(fn):
        raise AppObservationUnsupported("model_method_unavailable", stage, method)
    try:
        return fn(*args)
    except Exception:
        # Do not expose exception messages, object reprs, URLs, or document text.
        raise AppObservationUnsupported("model_api_call_failed", stage, method) from None


def _boolean(value, stage, api):
    if type(value) is not bool:
        raise AppObservationRefused("model_boolean_type_required", stage, api)
    return value


def _text(value, stage, api, limit, budget=None, nonempty=False):
    if type(value) is not str:
        raise AppObservationRefused("model_string_type_required", stage, api)
    if len(value) > limit:
        raise AppObservationRefused("model_string_limit", stage, api)
    if nonempty and not value:
        raise AppObservationUnsupported("empty_required_model_string", stage, api)
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise AppObservationRefused("invalid_unicode_scalar_string", stage, api) from None
    if budget is not None:
        budget[0] += len(value)
        if budget[0] > MAX_TOTAL_CODEPOINTS:
            raise AppObservationRefused("total_text_limit", stage, api)
    return value


def _property(obj, name, stage):
    info = _call(obj, "getPropertySetInfo", stage)
    available = _boolean(
        _call(info, "hasPropertyByName", stage, name), stage,
        "getPropertySetInfo.hasPropertyByName",
    )
    if not available:
        raise AppObservationUnsupported("required_model_property_unavailable", stage, name)
    return _call(obj, "getPropertyValue", stage, name)


def _bool_property(obj, name, stage):
    return _boolean(_property(obj, name, stage), stage, name)


def _supports(obj, service, stage):
    return _boolean(_call(obj, "supportsService", stage, service), stage, "supportsService")


def _more(enumeration, stage):
    return _boolean(_call(enumeration, "hasMoreElements", stage), stage, "hasMoreElements")


def _require_no_tables_or_fields(document):
    tables = _call(document, "getTextTables", "document.tables")
    count = _call(tables, "getCount", "document.tables")
    if type(count) is not int or count < 0:
        raise AppObservationRefused("model_nonnegative_count_required", "document.tables", "getCount")
    if count:
        raise AppObservationRefused("text_tables_outside_slice", "document.tables")
    fields = _call(document, "getTextFields", "document.fields")
    enumeration = _call(fields, "createEnumeration", "document.fields")
    if _more(enumeration, "document.fields"):
        raise AppObservationRefused("text_fields_outside_slice", "document.fields")


def _paragraph_text(paragraph, stage, budget):
    if not _supports(paragraph, "com.sun.star.text.Paragraph", stage):
        raise AppObservationRefused("nonparagraph_text_element", stage)
    text = _text(_call(paragraph, "getString", stage), stage, "getString",
                 MAX_TOTAL_CODEPOINTS, budget)
    enumeration = _call(paragraph, "createEnumeration", stage + ".portions")
    portion_strings = []
    portion_count = 0
    portion_codepoints = 0
    while _more(enumeration, stage + ".portions"):
        if portion_count >= MAX_PORTIONS_PER_PARAGRAPH:
            raise AppObservationRefused("text_portion_count_limit", stage)
        portion = _call(enumeration, "nextElement", stage + ".portions")
        portion_type = _text(_property(portion, "TextPortionType", stage + ".portions"),
                             stage, "TextPortionType", 64)
        if portion_type != "Text":
            raise AppObservationRefused("nontext_portion_outside_slice", stage, "TextPortionType")
        value = _text(_call(portion, "getString", stage + ".portions"), stage,
                      "portion.getString", MAX_TOTAL_CODEPOINTS)
        portion_codepoints += len(value)
        if portion_codepoints > MAX_TOTAL_CODEPOINTS:
            raise AppObservationRefused("text_portion_text_limit", stage)
        portion_strings.append(value)
        portion_count += 1
    if "".join(portion_strings) != text:
        raise AppObservationRefused("paragraph_portion_text_mismatch", stage)
    return text


def _paragraphs(text_object, stage, budget, *, body):
    enumeration = _call(text_object, "createEnumeration", stage)
    texts = []
    style_names = []
    limit = BODY_PARAGRAPHS if body else MAX_STORY_PARAGRAPHS
    while _more(enumeration, stage):
        if len(texts) >= limit:
            raise AppObservationRefused("paragraph_count_limit", stage)
        paragraph = _call(enumeration, "nextElement", stage)
        item_stage = stage + ".paragraph"
        texts.append(_paragraph_text(paragraph, item_stage, budget))
        if body:
            start = _call(paragraph, "getStart", item_stage)
            # This creates a local range cursor; no selection, navigation, or edit.
            cursor = _call(text_object, "createTextCursorByRange", item_stage, start)
            name = _text(_property(cursor, "PageStyleName", item_stage + ".page_style"),
                         item_stage, "PageStyleName", MAX_STYLE_NAME_CODEPOINTS,
                         nonempty=True)
            style_names.append(name)
    if body and len(texts) != BODY_PARAGRAPHS:
        raise AppObservationRefused("body_paragraph_count_outside_slice", stage)
    if not body and not texts:
        raise AppObservationRefused("empty_active_story_model", stage)
    return texts, style_names


def _story(page_style, prefix, budget):
    stage = "page_style." + prefix.lower()
    on = _bool_property(page_style, prefix + "IsOn", stage)
    if not on:
        # Retained disabled text is not active content. Do not read it.
        return {"is_on": False, "paragraphs": []}
    shared = _bool_property(page_style, prefix + "IsShared", stage)
    if not shared:
        raise AppObservationRefused("unshared_story_variants_outside_slice", stage)
    text_object = _property(page_style, prefix + "Text", stage)
    paragraphs, unused_names = _paragraphs(text_object, stage, budget, body=False)
    return {"is_on": True, "is_shared": True, "paragraphs": paragraphs}


def observe_loaded_writer(document, *, expected_url):
    """Return bounded plain JSON data from a passed already-loaded document.

    ``expected_url`` is only a local identity guard, not custody/provenance proof.
    No expected BODY/story values are accepted. ``observed`` means getter reads
    completed within this narrow shape; Root independently establishes real App,
    exact input, API semantics, process lifecycle, and expected-value comparison.
    Getter execution time is bounded by Root's external App lifecycle, not here.
    """
    base = {"schema": SCHEMA, "role": ROLE}
    try:
        expected_url = _text(expected_url, "argument", "expected_url",
                             MAX_URL_CODEPOINTS, nonempty=True)
        if not _supports(document, "com.sun.star.text.TextDocument", "document"):
            raise AppObservationRefused("not_writer_text_document", "document")
        url = _text(_call(document, "getURL", "document.location"),
                    "document.location", "getURL", MAX_URL_CODEPOINTS, nonempty=True)
        if url != expected_url:
            raise AppObservationRefused("loaded_document_url_mismatch", "document.location")
        has_location = _boolean(_call(document, "hasLocation", "document.location"),
                                "document.location", "hasLocation")
        readonly = _boolean(_call(document, "isReadonly", "document.readonly"),
                            "document.readonly", "isReadonly")
        _require_no_tables_or_fields(document)
        budget = [0]
        body = _call(document, "getText", "body")
        paragraphs, style_names = _paragraphs(body, "body", budget, body=True)
        effective_name = style_names[0]
        if any(name != effective_name for name in style_names):
            raise AppObservationRefused("multiple_effective_body_page_styles", "body.page_style")
        families = _call(document, "getStyleFamilies", "document.styles")
        page_styles = _call(families, "getByName", "document.styles", "PageStyles")
        page_style = _call(page_styles, "getByName", "page_style", effective_name)
        if not _supports(page_style, "com.sun.star.style.PageStyle", "page_style"):
            raise AppObservationRefused("not_page_style_service", "page_style")
        follow = _text(_property(page_style, "FollowStyle", "page_style"),
                       "page_style", "FollowStyle", MAX_STYLE_NAME_CODEPOINTS, nonempty=True)
        if follow != effective_name:
            raise AppObservationRefused("nonself_follow_page_style_outside_slice", "page_style")
        first_shared = _bool_property(page_style, "FirstIsShared", "page_style")
        if not first_shared:
            raise AppObservationRefused("unshared_first_page_stories_outside_slice", "page_style")
        header = _story(page_style, "Header", budget)
        footer = _story(page_style, "Footer", budget)
        return dict(base, status="observed", document={
            "service": "com.sun.star.text.TextDocument", "url": url,
            "has_location": has_location, "is_readonly": readonly,
        }, body={"paragraphs": paragraphs, "effective_page_style_names": style_names},
            default_page_stories={"page_style_name": effective_name,
                                  "follow_style_name": follow,
                                  "first_is_shared": first_shared,
                                  "header": header, "footer": footer})
    except AppObservationUnsupported as exc:
        return dict(base, status="unassessed", reason=exc.reason, stage=exc.stage, api=exc.api)
    except AppObservationRefused as exc:
        return dict(base, status="refused", reason=exc.reason, stage=exc.stage, api=exc.api)
