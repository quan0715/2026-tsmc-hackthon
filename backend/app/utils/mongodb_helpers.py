"""MongoDB 通用輔助函數

此模組提供整個 Backend 通用的 MongoDB 操作輔助函數，
避免在各個 Service 中重複相同的邏輯。
"""
from typing import Optional
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


def validate_and_convert_object_id(id_str: str, field_name: str = "id") -> Optional[ObjectId]:
    """驗證並轉換字串為 MongoDB ObjectId

    這是一個通用的 ID 驗證函數，用於將字串型別的 ID 轉換為 MongoDB ObjectId。
    如果轉換失敗，會記錄警告日誌並返回 None。

    Args:
        id_str: 要轉換的 ID 字串
        field_name: 欄位名稱（用於日誌記錄）

    Returns:
        ObjectId: 轉換成功返回 ObjectId 物件
        None: 轉換失敗返回 None

    Example:
        >>> obj_id = validate_and_convert_object_id("507f1f77bcf86cd799439011")
        >>> if obj_id:
        ...     result = await collection.find_one({"_id": obj_id})
    """
    try:
        return ObjectId(id_str)
    except Exception as e:
        logger.warning(
            f"無效的 {field_name}: {id_str}, 錯誤: {e.__class__.__name__}"
        )
        return None


def objectid_to_str(doc: dict, id_field: str = "_id") -> dict:
    """將文檔中的 ObjectId 轉換為字串

    MongoDB 查詢返回的文檔中 _id 欄位是 ObjectId 類型，
    需要轉換為字串才能在 Pydantic 模型中使用。

    Args:
        doc: MongoDB 文檔字典
        id_field: ObjectId 欄位名稱（預設為 "_id"）

    Returns:
        dict: 轉換後的文檔（會修改原始文檔）

    Example:
        >>> doc = await collection.find_one({"_id": ObjectId("...")})
        >>> doc = objectid_to_str(doc)
        >>> model = MyModel(**doc)
    """
    if doc and id_field in doc and isinstance(doc[id_field], ObjectId):
        doc[id_field] = str(doc[id_field])
    return doc


def build_update_dict(**kwargs) -> dict:
    """建立 MongoDB 更新字典

    自動過濾掉 None 值，並添加 updated_at 時間戳。

    Args:
        **kwargs: 要更新的欄位和值

    Returns:
        dict: 過濾後的更新字典

    Example:
        >>> from datetime import datetime
        >>> update = build_update_dict(
        ...     status="DONE",
        ...     error_message=None,  # 會被過濾掉
        ...     finished_at=datetime.utcnow()
        ... )
        >>> await collection.update_one({"_id": obj_id}, {"$set": update})
    """
    from datetime import datetime

    # 過濾掉 None 值
    update_dict = {k: v for k, v in kwargs.items() if v is not None}

    # 自動添加更新時間
    update_dict["updated_at"] = datetime.utcnow()

    return update_dict


class MongoDBQueryBuilder:
    """MongoDB 查詢建構器

    用於建構複雜的 MongoDB 查詢條件，避免手動拼接查詢字典。

    Example:
        >>> builder = MongoDBQueryBuilder()
        >>> query = (builder
        ...     .add_filter("project_id", "12345")
        ...     .add_filter("status", "RUNNING")
        ...     .add_date_range("created_at", start_date, end_date)
        ...     .build())
        >>> results = await collection.find(query).to_list(100)
    """

    def __init__(self):
        self.query = {}

    def add_filter(self, field: str, value, operator: str = "$eq"):
        """添加過濾條件

        Args:
            field: 欄位名稱
            value: 欄位值
            operator: MongoDB 運算符（預設 $eq）

        Returns:
            self: 支援鏈式呼叫
        """
        if value is not None:
            if operator == "$eq":
                self.query[field] = value
            else:
                self.query[field] = {operator: value}
        return self

    def add_in_filter(self, field: str, values: list):
        """添加 IN 過濾條件

        Args:
            field: 欄位名稱
            values: 值列表

        Returns:
            self: 支援鏈式呼叫
        """
        if values:
            self.query[field] = {"$in": values}
        return self

    def add_date_range(
        self,
        field: str,
        start_date=None,
        end_date=None
    ):
        """添加日期範圍過濾

        Args:
            field: 日期欄位名稱
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            self: 支援鏈式呼叫
        """
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            self.query[field] = date_filter
        return self

    def build(self) -> dict:
        """建構最終查詢字典

        Returns:
            dict: MongoDB 查詢字典
        """
        return self.query
