from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

T = TypeVar("T")


class CatchTableModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ApiEnvelope(CatchTableModel, Generic[T]):
    result_code: str | int | None = Field(
        default=None,
        validation_alias=AliasChoices("resultCode"),
    )
    display_message: str | None = Field(
        default=None,
        validation_alias=AliasChoices("displayMessage"),
    )
    message: str | None = None
    is_success: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("isSuccess"),
    )
    result_message: str | None = Field(
        default=None,
        validation_alias=AliasChoices("resultMessage"),
    )
    data: T | None = None


class AutocompleteSuggestion(CatchTableModel):
    item_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("itemType", "type"),
    )
    label: str | None = None
    matching_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("matchingCount", "count"),
    )
    shop_ref: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopRef", "itemRef", "ref"),
    )
    shop_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopUrl", "alias", "url"),
    )


class AutocompleteData(CatchTableModel):
    suggestions: list[AutocompleteSuggestion] = Field(
        default_factory=list,
        validation_alias=AliasChoices("suggestions", "items", "list"),
    )


class ValidUrlData(CatchTableModel):
    shop_ref: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopRef", "ref"),
    )
    shop_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopUrl", "alias", "url"),
    )
    is_valid: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("isValid", "valid"),
    )


class ShopDetail(CatchTableModel):
    shop_ref: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopRef", "id"),
    )
    shop_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopName", "name"),
    )
    shop_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopUrl", "alias", "url"),
    )
    food_kind_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("foodKindName", "foodKind", "categoryName", "category"),
    )
    shop_type_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopTypeName", "landName"),
    )
    road_address: str | None = Field(
        default=None,
        validation_alias=AliasChoices("roadAddress", "shopAddress", "address"),
    )
    lot_address: str | None = Field(
        default=None,
        validation_alias=AliasChoices("lotAddress", "shopAddress2", "jibunAddress"),
    )
    area_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("areaName"),
    )
    phone_number: str | None = Field(
        default=None,
        validation_alias=AliasChoices("phoneNumber", "shopPhone", "dispShopPhone", "tel"),
    )
    avg_rating: float | None = Field(
        default=None,
        validation_alias=AliasChoices("avgRating", "rating"),
    )
    review_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("reviewCount"),
    )
    scrap_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("scrapCount"),
    )
    short_introduction: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shortIntroduction", "serviceDesc", "description", "intro"),
    )
    lunch_price: str | None = Field(
        default=None,
        validation_alias=AliasChoices("lunchPriceText", "lunchPrice"),
    )
    dinner_price: str | None = Field(
        default=None,
        validation_alias=AliasChoices("dinnerPriceText", "dinnerPrice"),
    )
    latitude: float | None = Field(
        default=None,
        validation_alias=AliasChoices("latitude", "lat"),
    )
    longitude: float | None = Field(
        default=None,
        validation_alias=AliasChoices("longitude", "lon", "lng"),
    )


class DaySlot(CatchTableModel):
    visit_yymmdd: str | None = Field(
        default=None,
        validation_alias=AliasChoices("visitYymmdd", "date", "bookingDate"),
    )
    status_code: str | None = Field(
        default=None,
        validation_alias=AliasChoices("statusCode", "status"),
    )
    is_available: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("isAvailable", "available", "bookable"),
    )
    remaining_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("remainingCount", "availableCount", "count"),
    )
    holiday: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("isHoliday", "holiday"),
    )


class DaySlotsData(CatchTableModel):
    day_slots: list[DaySlot] = Field(
        default_factory=list,
        validation_alias=AliasChoices("daySlots", "slots", "items", "dates"),
    )


class SearchShop(CatchTableModel):
    shop_ref: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopRef", "id"),
    )
    shop_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shopName", "name"),
    )
    food_kind_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("foodKindName", "foodKind", "categoryName"),
    )
    land_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("landName", "areaName"),
    )
    road_address: str | None = Field(
        default=None,
        validation_alias=AliasChoices("roadAddress", "address"),
    )
    avg_rating: float | None = Field(
        default=None,
        validation_alias=AliasChoices("avgRating", "avgScore", "rating"),
    )
    review_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("reviewCount"),
    )

    @classmethod
    def from_shop_result(cls, shop_result: dict) -> SearchShop:
        """shopResults.shops[] 항목에서 shopMeta를 풀어서 생성."""
        meta = shop_result.get("shopMeta", shop_result)
        stats = meta.get("stats", {}) or {}
        return cls.model_validate({
            **meta,
            "reviewCount": stats.get("totalCount") or meta.get("reviewCount"),
            "avgRating": stats.get("avgTotalScore") or meta.get("avgScore"),
        })


class SearchListData(CatchTableModel):
    total_shop_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("totalShopCount", "totalCount", "total"),
    )
    shop_result_size: int | None = Field(
        default=None,
        validation_alias=AliasChoices("shopResultSize"),
    )
