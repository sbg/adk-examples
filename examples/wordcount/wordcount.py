import logging
from freyja import Automation, Step, Input, Output


class WordCounter(Step):
    line = Input(str)
    count = Output(int)

    def execute(self):
        self.count = len(self.line.strip().split())


class Main(Step):
    file_name = Input(str)

    def execute(self):
        with open(str(self.file_name), "r") as f:
            counts = [
                WordCounter(f"counter{idx}", line=line).count
                for idx, line in enumerate(f)
            ]

        logging.info(f"Found {sum(counts)} words.")


if __name__ == "__main__":
    Automation(Main).run()
