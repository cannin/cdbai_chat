import os
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch


def _install_stubs() -> None:
    class FakeDataFrame:
        def __init__(self, data=None):
            self._data = {k: list(v) for k, v in (data or {}).items()}

        def equals(self, other):
            return isinstance(other, FakeDataFrame) and self._data == getattr(other, "_data", None)

        def __len__(self):
            if not self._data:
                return 0
            first_col = next(iter(self._data.values()))
            return len(first_col)

        @property
        def empty(self):
            return len(self) == 0

        def __getitem__(self, key):
            return self._data[key]

        @property
        def shape(self):
            return (len(self), len(self._data))

        def to_csv(self, path, index=False):
            import csv

            headers = list(self._data.keys())
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(headers)
                for row in zip(*(self._data[h] for h in headers)):
                    writer.writerow(row)

    fake_pandas = ModuleType("pandas")
    fake_pandas.DataFrame = FakeDataFrame
    fake_pandas.Series = FakeDataFrame
    sys.modules.setdefault("pandas", fake_pandas)

    fake_numpy = ModuleType("numpy")
    fake_numpy.array = lambda x: x
    sys.modules.setdefault("numpy", fake_numpy)

    fake_scipy = ModuleType("scipy")
    fake_stats = ModuleType("scipy.stats")
    fake_stats.pearsonr = lambda x, y: (0.0, 1.0)
    fake_scipy.stats = fake_stats
    sys.modules.setdefault("scipy", fake_scipy)
    sys.modules.setdefault("scipy.stats", fake_stats)

    fake_sklearn = ModuleType("sklearn")
    fake_sklearn.__all__ = []
    sys.modules.setdefault("sklearn", fake_sklearn)

    fake_matplotlib = ModuleType("matplotlib")
    fake_pyplot = ModuleType("matplotlib.pyplot")
    fake_pyplot.switch_backend = lambda backend: None
    fake_pyplot.close = lambda *args, **kwargs: None
    fake_pyplot.savefig = lambda *args, **kwargs: None
    fake_pyplot.subplots = lambda *args, **kwargs: (SimpleNamespace(), SimpleNamespace())
    sys.modules.setdefault("matplotlib", fake_matplotlib)
    sys.modules.setdefault("matplotlib.pyplot", fake_pyplot)

    fake_seaborn = ModuleType("seaborn")
    fake_seaborn.heatmap = lambda *args, **kwargs: None
    sys.modules.setdefault("seaborn", fake_seaborn)

    fake_pil = ModuleType("PIL")

    class FakeImage:
        pass

    fake_pil.Image = FakeImage
    fake_pil_image = ModuleType("PIL.Image")
    fake_pil_image.Image = FakeImage
    sys.modules.setdefault("PIL", fake_pil)
    sys.modules.setdefault("PIL.Image", fake_pil_image)

    fake_litellm = ModuleType("litellm")

    def _stub_completion(*args, **kwargs):
        raise RuntimeError("litellm completion stub invoked")

    fake_litellm.completion = _stub_completion
    sys.modules.setdefault("litellm", fake_litellm)

    fake_dotenv = ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: True
    sys.modules.setdefault("dotenv", fake_dotenv)

    fake_flashtext = ModuleType("flashtext")

    class KeywordProcessor:
        def __init__(self, case_sensitive=False):
            self.case_sensitive = case_sensitive
            self._mapping = {}

        def add_keyword(self, keyword, replacement):
            key = keyword if self.case_sensitive else keyword.lower()
            self._mapping[key] = replacement

        def replace_keywords(self, text):
            result = text
            for key, repl in self._mapping.items():
                target = key if self.case_sensitive else key.lower()
                result = result.replace(target, repl)
            return result

    fake_flashtext.KeywordProcessor = KeywordProcessor
    sys.modules.setdefault("flashtext", fake_flashtext)

    fake_jinja2 = ModuleType("jinja2")

    class FakeEnvironment:
        def __init__(self, *args, **kwargs):
            pass

        def get_template(self, name):
            class _Template:
                def render(self, *args, **kwargs):
                    return ""

            return _Template()

    fake_jinja2.Environment = FakeEnvironment
    fake_jinja2.FileSystemLoader = lambda *args, **kwargs: None
    fake_jinja2.select_autoescape = lambda *args, **kwargs: None
    class FakeTemplate:
        def __init__(self, text):
            self._text = text

        def render(self, **context):
            rendered = self._text
            for key, value in context.items():
                rendered = rendered.replace(f"{{{{ {key} }}}}", str(value))
            return rendered

    fake_jinja2.Template = FakeTemplate
    sys.modules.setdefault("jinja2", fake_jinja2)

    fake_boto3 = ModuleType("boto3")
    fake_boto3.client = lambda name: SimpleNamespace(upload_file=lambda *args, **kwargs: None)
    sys.modules.setdefault("boto3", fake_boto3)

    fake_botocore = ModuleType("botocore")
    fake_botocore_exceptions = ModuleType("botocore.exceptions")

    class BotoCoreError(Exception):
        pass

    class ClientError(Exception):
        pass

    fake_botocore_exceptions.BotoCoreError = BotoCoreError
    fake_botocore_exceptions.ClientError = ClientError
    sys.modules.setdefault("botocore", fake_botocore)
    sys.modules.setdefault("botocore.exceptions", fake_botocore_exceptions)

    fake_google = ModuleType("google")
    fake_cloud = ModuleType("google.cloud")
    fake_bigquery = ModuleType("google.cloud.bigquery")
    fake_api_core = ModuleType("google.api_core")
    fake_api_core_exceptions = ModuleType("google.api_core.exceptions")

    class FakeBadRequest(Exception):
        pass

    fake_api_core_exceptions.BadRequest = FakeBadRequest

    class FakeQueryJobConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeBigQueryClient:
        def __init__(self, *args, **kwargs):
            pass

        def query(self, sql, job_config=None):
            return SimpleNamespace(to_dataframe=lambda: FakeDataFrame({}))

    fake_bigquery.Client = FakeBigQueryClient
    fake_bigquery.QueryJobConfig = FakeQueryJobConfig
    sys.modules.setdefault("google", fake_google)
    sys.modules.setdefault("google.cloud", fake_cloud)
    sys.modules.setdefault("google.cloud.bigquery", fake_bigquery)
    sys.modules.setdefault("google.api_core", fake_api_core)
    sys.modules.setdefault("google.api_core.exceptions", fake_api_core_exceptions)

    fake_service_account = ModuleType("google.oauth2.service_account")

    class FakeCredentials:
        @classmethod
        def from_service_account_file(cls, path):
            return SimpleNamespace()

    fake_service_account.Credentials = FakeCredentials
    fake_google_oauth2 = ModuleType("google.oauth2")
    sys.modules.setdefault("google.oauth2", fake_google_oauth2)
    sys.modules.setdefault("google.oauth2.service_account", fake_service_account)


_install_stubs()

import pandas as pd

import cdbai.pipeline as pipeline
from cdbai import utils


REQUIRED_ENV = {
    "GOOGLE_PROJECT_ID": "proj",
    "GOOGLE_DATASET": "cdbai",
    "GOOGLE_TABLE": "cdbai_20251005",
    "GOOGLE_APPLICATION_CREDENTIALS": "adc.json",
    "LITELLM_PROXY_API_BASE": "http://proxy",
    "AWS_S3_BUCKET": "bucket",
}


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(os.environ, REQUIRED_ENV, clear=True)
        self.env_patch.start()
        utils._get_bigquery_client.cache_clear()

    def tearDown(self):
        self.env_patch.stop()
        utils._get_bigquery_client.cache_clear()

    def test_check_required_env_vars_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(utils.MissingEnvironmentVariableError):
                utils.check_required_env_vars()

    def test_generate_sql_produces_base_query(self):
        with self.assertRaises(NotImplementedError):
            utils.generate_sql(
                "In CCLE what is the correlation of TP53 to MDM2 for CVCL_0002",
                normalized_prompt="in ccle what is the correlation of tp53 to mdm2 for cvcl_0002",
            )

    def test_upload_file_to_s3(self):
        uploaded = []

        class DummyClient:
            def upload_file(self, filename, bucket, key, ExtraArgs=None):
                uploaded.append((filename, bucket, key, ExtraArgs))

        with patch.object(utils.boto3, "client", return_value=DummyClient()):
            temp_dir = Path("tests/tmp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            image_path = temp_dir / "plot.png"
            image_path.write_bytes(b"fake")

            uri = utils.upload_file_to_s3(str(image_path))
            self.assertEqual(uri, "https://s3.us-east-1.amazonaws.com/bucket/plot.png")
            self.assertEqual(uploaded[0][3], None)

            uri = utils.upload_file_to_s3(str(image_path), content_type="image/png")
            self.assertEqual(uri, "https://s3.us-east-1.amazonaws.com/bucket/plot.png")
            self.assertEqual(uploaded[1][3], {"ContentType": "image/png"})

    def test_execute_sql_query_uses_client(self):
        df = pd.DataFrame({"a": [1, 2]})

        class DummyJob:
            def __init__(self, frame):
                self._frame = frame

            def to_dataframe(self):
                return self._frame

        class DummyClient:
            def __init__(self):
                self.queries = []

            def query(self, sql, job_config=None):
                self.queries.append((sql, job_config))
                return DummyJob(df)

        fake_credentials = MagicMock(return_value=SimpleNamespace())

        with patch.object(utils.service_account, "Credentials", SimpleNamespace(from_service_account_file=fake_credentials)):
            with patch.object(utils, "make_bq_client", return_value=DummyClient()):
                utils._get_bigquery_client.cache_clear()
                result = utils.execute_sql_query("SELECT 1")
                self.assertTrue(result.equals(df))

    def test_execute_sql_query_qualifies_table(self):
        df = pd.DataFrame({"a": [1]})

        class DummyJob:
            def __init__(self, frame):
                self._frame = frame

            def to_dataframe(self):
                return self._frame

        class DummyClient:
            def __init__(self):
                self.calls = 0
                self.queries = []

            def query(self, sql, job_config=None):
                self.calls += 1
                self.queries.append(sql)
                if self.calls == 1:
                    raise utils.BadRequest("Table \"cdbai_20251005\" must be qualified with a dataset")
                return DummyJob(df)

        fake_credentials = MagicMock(return_value=SimpleNamespace())

        with patch.object(utils.service_account, "Credentials", SimpleNamespace(from_service_account_file=fake_credentials)):
            with patch.object(utils, "make_bq_client", return_value=DummyClient()) as make_client:
                utils._get_bigquery_client.cache_clear()
                result = utils.execute_sql_query("SELECT * FROM cdbai_20251005")
                self.assertTrue(result.equals(df))
                client = make_client.return_value
                self.assertEqual(client.calls, 2)
                self.assertTrue(
                    "`proj.cdbai.cdbai_20251005`" in client.queries[-1]
                    or "`cdbai.cdbai_20251005`" in client.queries[-1]
                )


class RunCodeTestCase(unittest.TestCase):
    def setUp(self):
        env_with_prefix = dict(REQUIRED_ENV)
        env_with_prefix["RUN_OUTPUT_PREFIX"] = "test_"
        env_with_prefix["LOG_LEVEL"] = "DEBUG"
        self.env_patch = patch.dict(os.environ, env_with_prefix, clear=True)
        self.env_patch.start()
        Path("output").mkdir(exist_ok=True)
        for file in Path("output").glob("test_*"):
            try:
                file.unlink()
            except FileNotFoundError:
                pass

    def tearDown(self):
        self.env_patch.stop()
        for file in Path("output").glob("test_*"):
            try:
                file.unlink()
            except FileNotFoundError:
                pass

    def test_main_returns_string_result(self):
        uploads = []

        def fake_upload(path, content_type=None):
            uploads.append((Path(path).suffix.lower(), content_type))
            return f"https://s3.us-east-1.amazonaws.com/bucket/{Path(path).name}"

        with patch.object(pipeline, "check_required_env_vars", return_value=None), \
            patch.object(pipeline, "normalize_prompt", side_effect=lambda prompt: prompt.lower()), \
            patch.object(pipeline, "execute_sql_query", return_value=pd.DataFrame({"var_name": ["TP53", "MDM2"], "value": [0.1, 0.2]})), \
            patch.object(pipeline, "upload_file_to_s3", side_effect=fake_upload):

            code = (
                "sql = 'SELECT dataset, obs_name, var_name, value, tissue FROM table LIMIT 20;'\n"
                "df = execute_sql_query(sql)\n"
                "result = {\"type\": \"string\", \"value\": f'rows={len(df)}'}\n"
            )
            response = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=f"```python\n{code}\n```"))]
            )

            with patch.object(pipeline, "completion", return_value=response), \
                 patch.object(pipeline, "_maybe_correct_prompt", side_effect=lambda p: p):
                result = pipeline.cdbai_chat("In CCLE what is the correlation of TP53 to MDM2")
                self.assertEqual(result["type"], "string")
                self.assertTrue(result["value"].startswith("rows="))
                self.assertTrue(result.get("code", "").startswith("https://s3.us-east-1.amazonaws.com/bucket/test_tmp_"))
                self.assertTrue(result.get("csv", "").startswith("https://s3.us-east-1.amazonaws.com/bucket/test_tmp_"))
                self.assertTrue(result.get("normalized_prompt", "").startswith("in ccle what is the correlation"))
                self.assertEqual(result.get("original_prompt"), "In CCLE what is the correlation of TP53 to MDM2")
                self.assertIn((".py", "text/x-python"), uploads)
                self.assertIn((".csv", "text/csv"), uploads)
                self.assertIn((".txt", "text/plain"), uploads)

    def test_main_uploads_plot(self):
        uploads = []

        def fake_upload(path, content_type=None):
            uploads.append((Path(path).suffix.lower(), content_type))
            return f"https://s3.us-east-1.amazonaws.com/bucket/{Path(path).name}"

        with patch.object(pipeline, "check_required_env_vars", return_value=None), \
            patch.object(pipeline, "normalize_prompt", side_effect=lambda prompt: prompt.lower()), \
            patch.object(pipeline, "execute_sql_query", return_value=pd.DataFrame({"x": [1]})), \
            patch.object(pipeline, "upload_file_to_s3", side_effect=fake_upload), \
            patch.object(pipeline, "_maybe_correct_prompt", side_effect=lambda p: p):

            code = (
                "import pathlib\n"
                "df = execute_sql_query('SELECT dataset, obs_name, var_name, value, tissue FROM table LIMIT 10;')\n"
                "png_path = allocate_plot_png_path()\n"
                "svg_path = allocate_plot_svg_path(png_path)\n"
                "pathlib.Path(png_path).write_bytes(b'fake')\n"
                "pathlib.Path(svg_path).write_bytes(b'fake')\n"
                "result = {\"type\": \"plot\", \"value\": upload_file_to_s3(png_path), \"svg\": upload_file_to_s3(svg_path)}\n"
            )
            response = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=f"```python\n{code}\n```"))]
            )

            with patch.object(pipeline, "completion", return_value=response):
                result = pipeline.cdbai_chat("show plot")
                self.assertEqual(result["type"], "plot")
                self.assertTrue(result["value"].startswith("https://s3.us-east-1.amazonaws.com/bucket/test_tmp_"))
                self.assertTrue(result["code"].startswith("https://s3.us-east-1.amazonaws.com/bucket/test_tmp_"))
                self.assertTrue(result["csv"].startswith("https://s3.us-east-1.amazonaws.com/bucket/test_tmp_"))
                self.assertTrue(result["svg"].startswith("https://s3.us-east-1.amazonaws.com/bucket/test_tmp_"))
                self.assertIn((".png", "image/png"), uploads)
                self.assertIn((".svg", "image/svg+xml"), uploads)
                self.assertIn((".py", "text/x-python"), uploads)

    def test_double_extension_artifacts_are_canonicalized(self):
        run_id = "20251013T192123"
        prev_run_id = pipeline._RUN_ID
        prev_prefix = pipeline.RUN_OUTPUT_PREFIX
        pipeline._RUN_ID = run_id
        pipeline.RUN_OUTPUT_PREFIX = "test_"
        png_double = Path(f"output/test_tmp_{run_id}.png.png")
        svg_double = Path(f"output/test_tmp_{run_id}.png.svg")
        png_double.write_bytes(b"png")
        svg_double.write_bytes(b"svg")

        uploaded = []

        def fake_upload(path, content_type=None):
            path_obj = Path(path)
            uploaded.append((path_obj.name, content_type))
            return f"https://s3.us-east-1.amazonaws.com/bucket/{path_obj.name}"

        try:
            with patch.object(pipeline, "upload_file_to_s3", side_effect=fake_upload):
                uploads = pipeline._upload_artifacts_to_s3()

            expected_png = f"test_tmp_{run_id}.png"
            expected_svg = f"test_tmp_{run_id}.svg"
            self.assertIn("plot", uploads)
            self.assertEqual(
                uploads["plot"][0],
                f"https://s3.us-east-1.amazonaws.com/bucket/{expected_png}",
            )
            self.assertIn("svg", uploads)
            self.assertEqual(
                uploads["svg"][0],
                f"https://s3.us-east-1.amazonaws.com/bucket/{expected_svg}",
            )
            self.assertEqual(sorted(name for name, _ in uploaded), [expected_png, expected_svg])
            self.assertIn((expected_png, "image/png"), uploaded)
            self.assertIn((expected_svg, "image/svg+xml"), uploaded)
            self.assertTrue(Path(f"output/{expected_png}").exists())
            self.assertTrue(Path(f"output/{expected_svg}").exists())
            self.assertFalse(png_double.exists())
            self.assertFalse(svg_double.exists())
        finally:
            pipeline._RUN_ID = prev_run_id
            pipeline.RUN_OUTPUT_PREFIX = prev_prefix
            for leftover in Path("output").glob(f"test_tmp_{run_id}*"):
                try:
                    leftover.unlink()
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    unittest.main()
