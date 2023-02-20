import shutil
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import urlretrieve

import PyPDF2
import requests
from bs4 import BeautifulSoup


def download(url: str, save_dir: Path):
    if not save_dir.exists():
        raise NameError("保存先のディレクトリは存在しません")

    res = requests.get(url)
    res.raise_for_status()

    soup = BeautifulSoup(res.content, "html.parser")

    # 本のタイトル
    title = soup.find("h3", class_="title").text
    title = title.replace(" ", "_")

    # 保存するパス
    save_path = save_dir.joinpath(f"{title}.pdf")
    if save_path.exists():
        raise FileExistsError(f"{save_path}はすでに存在しています")

    for div in soup.find_all("div"):
        if not div.h3:
            continue
        if div.h3.text != "Contents":
            continue

        pdf_chapter_filenames = [a["href"] for a in div.find_all("a")]
        break

    tmp_dir = Path("tmp").resolve()
    tmp_dir.mkdir(exist_ok=True)

    # 各章のPDFをダウンロード
    for i, filename in enumerate(pdf_chapter_filenames):
        pdf_url = urljoin(url, filename)
        save_path = tmp_dir.joinpath(f"{i}_{filename}")
        try:
            urlretrieve(pdf_url, save_path)
        except HTTPError as e:
            raise NameError(f"{pdf_url}のリンクが切れています\n{e}")

    # 各章をまとめて保存
    merger = PyPDF2.PdfMerger()
    for pdf_chapter in tmp_dir.glob("*"):
        merger.append(pdf_chapter)
    merger.write(save_path)
    merger.close()

    # 各章のPDFを削除
    shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    url = "https://www.oreilly.co.jp/library/4873112699/"
    save_dir = Path.home().joinpath("Downloads")
    download(url, save_dir)
