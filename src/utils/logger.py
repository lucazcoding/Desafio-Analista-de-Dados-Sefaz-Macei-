import logging
import sys

import pandas as pd


def configurar_logging() -> None:
    """Configura logging, exibição do pandas e encoding UTF-8."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    pd.options.display.float_format = "{:,.2f}".format

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
