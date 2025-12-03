import argparse
import csv
import os
from typing import Any, List, Tuple

from tabulate import tabulate


class CSVReader:
    """
    Читает CSV-файл и возвращает данные в виде списка списков.
    """

    @staticmethod
    def read(file_path: str) -> List[List[str]]:
        """
        Считывает CSV-файл.

        Args:
            file_path: Путь к файлу.

        Returns:
            Данные из файла в виде списка списков строк.

        Raises:
            ValueError: Если файл не .csv.
            FileNotFoundError: Если файл не найден.
        """
        if not file_path.endswith(".csv"):
            raise ValueError(f"Файл должен быть в формате .csv: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return list(csv.reader(f))


class Report:
    """
    Генерирует отчёты на основе CSV-данных.
    Новые отчёты добавляются как staticmethod с именем, совпадающим с именем
    отчёта.
    """

    @classmethod
    def generate(
            cls, report_name: str, data: List[List[str]]
    ) -> Tuple[List[str], List[List[Any]]]:
        """
        Диспетчер отчётов.

        Args:
            report_name: Имя отчёта.
            data: Данные CSV.

        Returns:
            (headers, report_data)

        Raises:
            ValueError: Если отчёт не найден.
        """
        method = getattr(cls, report_name, None)
        if not method or not callable(method):
            raise ValueError(f"Отчёт '{report_name}' не найден.")

        return method(data)

    @staticmethod
    def performance(data: List[List[str]]) -> Tuple[List[str], List[List[Any]]]:
        """
        Отчёт средняя производительность.
        Группирует по 'position', считает среднее по 'performance',
        сортирует по убыванию.

        Args:
            data: Список строк CSV, включая заголовки.

        Returns:
            Заголовки и отсортированные данные: [№, position, performance]
        """
        headers = data[0]
        rows = data[1:]

        try:
            pos_idx = headers.index("position")
            perf_idx = headers.index("performance")
        except ValueError as e:
            raise ValueError(f"Отсутствует колонка: {e.args[0]}")

        perf_data: dict[str, list[float]] = {}
        for row in rows:
            position = row[pos_idx]
            performance = float(row[perf_idx])

            if position not in perf_data:
                perf_data[position] = []
            perf_data[position].append(performance)

        result = [
            [pos, f"{sum(perf) / len(perf):.2f}"] for pos, perf in
            perf_data.items()
        ]
        result.sort(key=lambda x: float(x[1]), reverse=True)

        result = [[str(i + 1), *row] for i, row in enumerate(result)]
        return ["№", "position", "performance"], result


class ReportPrinter:
    """
    Выводит отчёт в консоль.
    """

    def __init__(self, headers: List[str], data: List[List[Any]]) -> None:
        self.headers = headers
        self.data = data

    def print(self) -> None:
        print(tabulate(self.data, headers=self.headers, disable_numparse=True))


class Main:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--files", nargs="+", required=True)
        self.parser.add_argument("--report", required=True)

        self.args = self.parser.parse_args()

    def run(self):
        all_data: List[List[str]] = []

        for file_path in self.args.files:
            if not os.path.exists(file_path):
                self.parser.error(f"Файл не найден: {file_path}")
            try:
                data = CSVReader.read(file_path)
                if not all_data:
                    all_data = data
                else:
                    all_data.extend(data[1:])
            except Exception as e:
                self.parser.error(f"Ошибка при чтении файла {file_path}: {e}")

        try:
            headers, report_data = Report.generate(self.args.report, all_data)
        except ValueError as e:
            self.parser.error(f"Ошибка при генерации отчёта: {e}")

        printer = ReportPrinter(headers, report_data)
        printer.print()


if __name__ == "__main__":
    main = Main()
    main.run()
