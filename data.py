# -*- coding: utf-8 -*-
# @Time         : 20:41 2022/12/16
# @Author       : Chris
# @Description  :
import base64
import json
import os.path
import uuid
from pathlib import Path
from typing import Union, List, Tuple
from copy import deepcopy
import io
import zipfile
from PIL import Image
from .path import realpath


def zip_coco2bytes(coco_data: Union[dict, str]) -> bytes:
    """Zip COCO to bytes. Images are packed too."""
    if isinstance(coco_data, dict):  # In memory coco dict.
        with io.BytesIO() as buffer:
            with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                images = []
                for img_dict in coco_data["images"]:
                    img_dict_copy = deepcopy(img_dict)
                    raw_img_path = img_dict_copy["file_name"]
                    img_path = realpath(raw_img_path)
                    file_name = os.path.basename(img_path)
                    new_img_path = f"images/{file_name}"
                    zf.write(img_path, new_img_path)
                    img_dict_copy["file_name"] = file_name
                    images.append(img_dict_copy)
                org_images = coco_data["images"]
                coco_data["images"] = images  # Make new data for zipping.
                zf.writestr("annotations.json", json.dumps(coco_data, ensure_ascii=True))
                coco_data["images"] = org_images  # Recover original data.
            return buffer.getvalue()
    elif isinstance(coco_data, str):
        with open(coco_data, "r", encoding="utf-8") as f:
            coco_dict = json.load(f)
        return zip_coco2bytes(coco_dict)
    else:
        raise NotImplementedError(f"Unsupported coco data type '{coco_data}'!")


def zip_files2bytes(files: Union[list, dict]) -> bytes:
    """
    When files is of type 'list': Gather all files in the list and zip them. Entry name is flatted as file <idx>_name.
    :param files:
    :return:
    """
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, True) as zf:
            if isinstance(files, list):
                for i in range(len(files)):
                    file_path = files[i]
                    file_name = os.path.basename(file_path)
                    zf.write(file_path, f"{i}_{file_name}")
            else:
                raise NotImplementedError()
        return buffer.getvalue()


def zip_data2bytes(data: List[Union[str, dict, Image.Image]]):
    """
    Zip a list of data item to bytes.
    :param data: List of data item. Data item can be:
        1. 'str': Means file path (Maybe in LabelStudio style).
        2. 'dict' with key 'b64': Bytes encoded in base64.
    :return:
    """
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, True) as zf:
            for item in data:
                if isinstance(item, str):  # File path.
                    file_name = os.path.basename(item)
                    zf.write(realpath(item), file_name)
                elif isinstance(item, Image.Image):  # Image.
                    im_buffer = io.BytesIO()
                    item.save(im_buffer, "JPEG")
                    zf.writestr(str(uuid.uuid4())+".jpg", im_buffer.getvalue())
                elif isinstance(item, dict):  # Data dict.
                    b64_str = item.get("b64")
                    if b64_str is not None:
                        item_bytes = base64.b64decode(b64_str)
                    else:
                        raise NotImplementedError(f"Unsupported data dict '{item}'.")
                    item_name = item.get("name") or str(uuid.uuid4())
                    zf.writestr(item_name, item_bytes)
                else:
                    raise NotImplementedError(f"Unknown data '{item}(type={type(item)})'.")
        return buffer.getvalue()


def iter_files_from_zip_bytes(zip_bytes: bytes) -> List[Tuple[str, bytes]]:
    """
    Iterate file from zip file bytes.
    :param zip_bytes:
    :return: [(file_name1, file_bytes1), ...]
    """
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r", zipfile.ZIP_DEFLATED, False)
    for fileinfo in zf.infolist():
        yield fileinfo.filename, zf.read(fileinfo)


def unzip_bytes(zip_bytes: bytes, output_dir: str):
    """
    Unzip zip bytes to disk files.
    :param zip_bytes:
    :param output_dir:
    :return:
    """
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    zf.extractall(output_dir)


def zip_dir2bytes(dir_path: str):
    """Zip a directory and its files to bytes. Sub dir included."""
    dir = Path(dir_path)
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for entry in dir.rglob("*"):
                zip_file.write(entry, entry.relative_to(dir))
        return buffer.getvalue()


def iter_files4zip_bytes(zip_bytes: bytes) -> List[Tuple[str, bytes]]:
    """
    Iterate file from zip file bytes.
    :param zip_bytes:
    :return: [(file_name1, file_bytes1), ...]
    """
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r", zipfile.ZIP_DEFLATED, False)
    for fileinfo in zf.infolist():
        yield fileinfo.filename, zf.read(fileinfo)


def unzip_bytes2dir(zip_bytes: bytes, output_dir: str):
    """
    Unzip zip bytes to disk files.
    :param zip_bytes:
    :param output_dir:
    :return:
    """
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    zf.extractall(output_dir)


class NestedListFlatter:
    """Flat nested list, rehabilitate flatted list to nested list."""
    def __init__(self, nested_list: list, max_leaf_level=99999999):
        """Object at a level at max_leaf_level will be treated as item. Root list is of level 0."""
        self._nested_list = nested_list
        self._max_leaf_level = max_leaf_level

    def flat(self):
        """Flat nested list into 1-D list."""
        flatted = []
        self._r_flat(self._nested_list, flatted, 0, self._max_leaf_level)
        return flatted

    def rehabilitate(self, flatted: list):
        """Rehabilitate the flatted list to nested list that
        has a same structure with the target list of this flatter."""
        return self._r_rehabilitate(flatted, [0], self._nested_list, 0, self._max_leaf_level)

    @staticmethod
    def _r_rehabilitate(flatted: list, idx: List[int], node, depth: int, max_depth: int):
        if isinstance(node, list) and depth < max_depth:
            return [NestedListFlatter._r_rehabilitate(flatted, idx, child, depth+1, max_depth) for child in node]
        else:
            item = flatted[idx[0]]
            idx[0] += 1
            return item

    @staticmethod
    def _r_flat(node, flatted: list, depth: int, max_depth: int):
        if isinstance(node, list) and depth < max_depth:
            for child in node:
                NestedListFlatter._r_flat(child, flatted, depth+1, max_depth)
        else:
            flatted.append(node)
