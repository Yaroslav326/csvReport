import pytest
from main import CSVReader, Report, ReportPrinter, Main
from unittest.mock import patch, MagicMock


class TestCSVReader:
    def test_read_csv(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            """name,position,performance
Alice,Developer,4.5
Bob,Manager,4.8""",
            encoding="utf-8"
        )

        data = CSVReader.read(str(csv_file))
        assert data == [
            ["name", "position", "performance"],
            ["Alice", "Developer", "4.5"],
            ["Bob", "Manager", "4.8"]
        ]

    def test_read_non_csv_file(self):
        with pytest.raises(ValueError,
                           match="Файл должен быть в формате .csv: data.txt"):
            CSVReader.read("data.txt")

    def test_read_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            CSVReader.read("nonexistent.csv")


class TestReport:
    @pytest.fixture
    def sample_data(self):
        return [
            ["name", "position", "performance"],
            ["Alice", "Backend", "4.8"],
            ["Bob", "Backend", "5.0"],
            ["Charlie", "Frontend", "4.4"],
            ["Diana", "Frontend", "4.6"],
        ]

    def test_performance_report(self, sample_data):
        headers, data = Report.performance(sample_data)
        assert headers == ["№", "position", "performance"]
        assert data == [
            ["1", "Backend", "4.90"],
            ["2", "Frontend", "4.50"]
        ]

    def test_performance_position_column(self):
        data = [["name", "perf"], ["Alice", "4.5"]]
        with pytest.raises(ValueError, match="Отсутствует колонка: "
                                             "'position' is not in list"):
            Report.performance(data)

    def test_invalid_performance_value(self, sample_data):
        invalid_data = sample_data
        invalid_data[1][-1] = "not_a_number"
        with pytest.raises(ValueError):
            Report.performance(invalid_data)

    def test_generate_report(self, sample_data):
        headers, data = Report.generate("performance", sample_data)
        assert headers == ["№", "position", "performance"]
        assert len(data) == 2

    def test_generate_report_not_found(self, sample_data):
        with pytest.raises(ValueError, match="Отчёт 'unknown' не найден."):
            Report.generate("unknown", sample_data)


class TestReportPrinter:
    def test_print_report(self, capsys):
        headers = ["№", "position", "performance"]
        data = [["1", "Backend", "4.90"], ["2", "Frontend", "4.60"]]
        printer = ReportPrinter(headers, data)
        printer.print()

        captured = capsys.readouterr()
        output = captured.out.strip()

        assert "1" in output
        assert "Backend" in output
        assert "4.90" in output
        assert "Frontend" in output
        assert "performance" in output
        assert "---" in output


class TestMain:
    @patch("main.ReportPrinter")
    @patch("main.Report.generate")
    @patch("main.CSVReader.read")
    @patch("os.path.exists")
    def test_main_run_success(self, mock_exists, mock_read, mock_generate,
                              mock_printer):
        mock_exists.return_value = True

        mock_read.return_value = [
            ["name", "position", "performance"],
            ["Alice", "Backend", "4.8"]
        ]

        mock_generate.return_value = (["№", "position"], [["1", "Backend"]])
        mock_printer_instance = MagicMock()
        mock_printer.return_value = mock_printer_instance

        with patch("sys.argv",
                   ["main.py", "--files", "dummy1.csv", "dummy2.csv",
                    "--report", "performance"]):
            main = Main()
            main.run()

        assert mock_read.call_count == 2
        mock_generate.assert_called_once_with("performance",
                                              mock_read.return_value)
        mock_printer_instance.print.assert_called_once()

    @patch("main.CSVReader.read")
    def test_main_file_not_found(self, mock_read):
        mock_read.side_effect = FileNotFoundError("No such file")

        with patch("sys.argv", ["main.py", "--files", "missing.csv",
                                "--report", "performance"]):
            with patch("argparse.ArgumentParser.error",
                       side_effect=SystemExit) as mock_error:
                with pytest.raises(SystemExit):
                    main = Main()
                    main.run()
                mock_error.assert_called()

    @patch("main.CSVReader.read")
    def test_main_read_error(self, mock_read):
        mock_read.side_effect = ValueError("Invalid CSV")

        with patch("sys.argv", ["main.py", "--files", "bad.csv", "--report",
                                "performance"]):
            with patch("argparse.ArgumentParser.error",
                       side_effect=SystemExit) as mock_error:
                with pytest.raises(SystemExit):
                    main = Main()
                    main.run()
                mock_error.assert_called()

    @patch("main.Report.generate")
    @patch("main.CSVReader.read")
    def test_main_report_not_found(self, mock_read, mock_generate):
        mock_read.return_value = [["name", "position", "performance"],
                                  ["Alice", "Backend", "4.8"]]
        mock_generate.side_effect = ValueError("Отчёт 'unknown' не найден.")

        with patch("sys.argv", ["main.py", "--files", "data.csv", "--report",
                                "unknown"]):
            with patch("argparse.ArgumentParser.error",
                       side_effect=SystemExit) as mock_error:
                with pytest.raises(SystemExit):
                    main = Main()
                    main.run()
                mock_error.assert_called()
