import os
import sys

# Cho phep chay truc tiep file nay (vd. khi khoi dong cung Windows): them thu muc cha vao duong dan
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from screentrans.app import main  # noqa: E402

if __name__ == "__main__":
    main()
