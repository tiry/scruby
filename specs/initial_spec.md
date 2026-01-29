## Goal

I want to create a Python CLI tool called **`scruby`** (using `click`) to process and redact text data.

---

## Redaction

The CLI must be able to redact all **18 HIPAA PII identifiers**.

* Entity detection will be done using **Microsoft Presidio** (which relies on **spaCy**).
* For each detected entity, we will:

  1. **Normalize** the entity string (trim, lowercase, ASCII)
  2. Replace it in the text with:

```
<entity_type>:<sha1(normalized_entity)>
```

---

## Processing Pipeline

Execution is based on a pipeline with the following steps:

1. **READ**: Read the next document
2. **PRE-PROCESSING**: Extract one or more text fields to redact
3. **REDACT**: Detect + redact entities in those fields
4. **POST-PROCESSING**: Merge redacted fields back into the original document
5. **SAVE**: Save the redacted document

Each operation must be **pluggable**:

* Use an **abstract Python class** for each step
* Use a **registry** per step (map `name -> implementation`)
* Use a **factory** to instantiate the chosen implementation

---

## Step Details

### READ

* Read all files from the source.
* Output must be a Python `dict`.
* Default reader/writer: simple text files in a folder, represented as:

```python
{"content": "..."}
```

* The default reader must support:

  * a single file
  * all files in a folder

---

### PRE-PROCESSING

* Extract fields to redact from the raw document.
* Return a **sub-dictionary** containing only the fields to redact.

---

### REDACT

* Use:

  * `presidio-analyzer`
  * `presidio-anonymizer`
  * `spaCy`

Redaction rules:

* Use a **keyed hash (HMAC)** for anonymization.
* The **salt / secret key** (to prevent rainbow table attacks) is provided via configuration.
* Normalization is applied **only to the extracted entity span**, before hashing — not to the source text.
* Overlapping spans must be handled using Presidio anonymizer logic:

  * prioritize **longest match**, or
  * highest **confidence score**

Output:

* Return a dictionary containing the redacted values.

---

### POST-PROCESSING

* Update the original document with the redacted fields.

---

### SAVE

* Default writer: save as a text file in an output folder.

---

## CLI

The CLI must support:

* `--reader` : select the reader implementation by name
* `--writer` : select the writer implementation by name
* `--src` : source path or URI
* `--out` : destination path or URI
* `--config` : config file path (default: `config.yaml`)
* `--max` : max number of files to process (default: `-1` = all)
* `--dry-run` : show what would be redacted without saving
* `--threshold` : min confidence score for Presidio
* `--log-stats` : export a CSV with counts per HIPAA entity type

If no destination is provided, output should be written to **stdout**.

---

## Configuration

The YAML config file must provide:

* the salt/secret key used for the HMAC
* the default minimum confidence score

We also need a Python module: **`presidio_config.py`**, which defines:

* supported entities for `AnalyzerEngine`
* operators for `AnonymizerEngine`

Since some identifiers are not built-in (e.g. **MRN**, **Health Plan IDs**, **Certificate/License Numbers**, **Vehicle VINs**), we must implement custom `PatternRecognizer` instances (regex-based) for those entities in `presidio_config.py`.

