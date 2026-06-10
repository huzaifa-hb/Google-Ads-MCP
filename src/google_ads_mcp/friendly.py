"""Dispatcher for friendly Google Ads MCP tool names."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .gaql import (
    DEFAULT_DATE_RANGE,
    TIME_SEGMENTS,
    build_filter_clauses,
    date_where_clause,
    gaql_literal,
    select_clause,
)
from .gateway import GoogleAdsGateway
from .geo_targets import resolve_geo_target
from .safety import CONFIRMATION_PHRASE, ValidationError, normalize_customer_id, validate_date
from .tool_catalog import FriendlyToolSpec, FRIENDLY_TOOL_BY_NAME
from .tool_implementation import (
    AD_GROUP_STATUS_TOOLS,
    AD_STATUS_TOOLS,
    APPLY_LABEL_TOOLS,
    ASSET_MUTATION_TOOLS,
    BUDGET_CREATE_TOOLS,
    BUDGET_UPDATE_TOOLS,
    CAMPAIGN_BULK_STATUS_TOOLS,
    CAMPAIGN_CHANNEL_BY_CREATE_TOOL,
    CAMPAIGN_CREATE_TOOLS,
    CAMPAIGN_STATUS_TOOLS,
    KEYWORD_BID_TOOLS,
    KEYWORD_CREATE_TOOLS,
    KEYWORD_STATUS_TOOLS,
    REMOVE_LABEL_FROM_TOOLS,
)


DEFAULT_REPORT_DATE_RANGE = "LAST_30_DAYS"
CHANGE_EVENT_DEFAULT_DATE_RANGE = "LAST_14_DAYS"


class FriendlyDispatcher:
    """Route named friendly tools to generic Google Ads API primitives."""

    def __init__(self, gateway: GoogleAdsGateway | None = None) -> None:
        self.gateway = gateway or GoogleAdsGateway()

    async def dispatch(
        self,
        tool_name: str,
        *,
        customer_id: str | int | None = None,
        payload: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        date_range: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        time_segment: str | None = None,
        max_rows: int | None = 1000,
        max_accounts: int | None = None,
        page_size: int | None = None,
        page_token: str | None = None,
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
        partial_failure: bool = False,
    ) -> dict[str, Any]:
        spec = FRIENDLY_TOOL_BY_NAME[tool_name]
        payload = payload or {}
        filters = filters or {}

        if spec.mode == "unsupported":
            return self._unsupported(spec)
        if spec.mode == "raw_gaql":
            return await self._raw_gaql(
                customer_id=customer_id,
                payload=payload,
                max_rows=max_rows,
                page_size=page_size,
                page_token=page_token,
            )
        if spec.mode == "query":
            return await self._query(
                spec,
                customer_id=customer_id,
                payload=payload,
                filters=filters,
                max_rows=max_rows,
                max_accounts=max_accounts,
                page_size=page_size,
                page_token=page_token,
            )
        if spec.mode == "report":
            return await self._report(
                spec,
                customer_id=customer_id,
                payload=payload,
                filters=filters,
                date_range=date_range,
                start_date=start_date,
                end_date=end_date,
                time_segment=time_segment,
                max_rows=max_rows,
                page_size=page_size,
                page_token=page_token,
            )
        if spec.mode == "negative_keyword":
            return await self._negative_keyword(
                spec,
                customer_id=customer_id,
                payload=payload,
                filters=filters,
                max_rows=max_rows,
                page_size=page_size,
                page_token=page_token,
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
                partial_failure=partial_failure,
            )
        if spec.mode == "service":
            return await self._service(
                spec,
                customer_id=customer_id,
                payload=payload,
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
            )
        return await self._mutate(
            spec,
            customer_id=customer_id,
            payload=payload,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            partial_failure=partial_failure,
        )

    async def _raw_gaql(
        self,
        *,
        customer_id: str | int | None,
        payload: dict[str, Any],
        max_rows: int | None,
        page_size: int | None,
        page_token: str | None,
    ) -> dict[str, Any]:
        cid = self._require_customer_id(customer_id, payload)
        query = payload.get("query")
        if not query:
            raise ValidationError("execute_gaql_query requires payload.query.")
        return await self.gateway.search(
            customer_id=cid,
            query=query,
            max_rows=max_rows,
            page_size=page_size,
            page_token=page_token,
            primary_field=payload.get("primary_field"),
        )

    async def _query(
        self,
        spec: FriendlyToolSpec,
        *,
        customer_id: str | int | None,
        payload: dict[str, Any],
        filters: dict[str, Any],
        max_rows: int | None,
        max_accounts: int | None,
        page_size: int | None,
        page_token: str | None,
    ) -> dict[str, Any]:
        cid = self._require_customer_id(customer_id, payload)
        if spec.name == "get_mcc_hierarchy":
            return await self._mcc_hierarchy(
                root_customer_id=cid,
                payload=payload,
                max_accounts=max_accounts,
                page_size=page_size,
                page_token=page_token,
            )
        if spec.name == "list_customers" and not payload.get("include_managers"):
            filters = {**filters, "customer_client.manager": False}
        warnings: list[str] = []
        clauses = await self._filter_clauses_for_resource(spec.resource, filters, warnings)
        query = self._build_query(spec, payload=payload, clauses=clauses)
        result = await self.gateway.search(
            customer_id=cid,
            query=query,
            max_rows=max_rows,
            page_size=page_size,
            page_token=page_token,
            primary_field=spec.primary_field,
        )
        self._attach_warnings(result, warnings)
        return result

    async def _report(
        self,
        spec: FriendlyToolSpec,
        *,
        customer_id: str | int | None,
        payload: dict[str, Any],
        filters: dict[str, Any],
        date_range: str | None,
        start_date: str | None,
        end_date: str | None,
        time_segment: str | None,
        max_rows: int | None,
        page_size: int | None,
        page_token: str | None,
    ) -> dict[str, Any]:
        cid = self._require_customer_id(customer_id, payload)
        fields = list(spec.fields)
        if time_segment:
            segment_field = TIME_SEGMENTS.get(time_segment)
            if not segment_field:
                allowed = ", ".join(sorted(TIME_SEGMENTS))
                raise ValidationError(f"Unknown time_segment '{time_segment}'. Allowed: {allowed}.")
            if segment_field not in fields:
                fields.append(segment_field)

        if "segments.hour" in fields and "segments.date" not in fields:
            fields.append("segments.date")

        warnings: list[str] = []
        clauses = await self._filter_clauses_for_resource(spec.resource, filters, warnings)
        effective_date_range = self._effective_report_date_range(
            spec,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
        )
        if spec.resource == "change_event":
            self._validate_change_event_range(effective_date_range, start_date, end_date)
        date_clause = date_where_clause(
            date_range=effective_date_range,
            start_date=start_date,
            end_date=end_date,
            field=self._report_date_field(spec.resource),
        )
        if date_clause:
            clauses.append(date_clause)

        query = f"{select_clause(fields)} FROM {spec.resource}"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        result = await self.gateway.search(
            customer_id=cid,
            query=query,
            max_rows=max_rows,
            page_size=page_size,
            page_token=page_token,
            primary_field=spec.primary_field,
        )
        self._attach_warnings(result, warnings)
        if spec.name == "get_geo_performance":
            for row in result.get("rows", []):
                geo = row.get("geographic_view", {})
                for key, criterion_id in list(geo.items()):
                    if key.endswith("criterion_id") and criterion_id:
                        geo[f"{key.removesuffix('_criterion_id')}_name"] = resolve_geo_target(
                            criterion_id
                        )
        return result

    async def _mutate(
        self,
        spec: FriendlyToolSpec,
        *,
        customer_id: str | int | None,
        payload: dict[str, Any],
        validate_only: bool,
        execute: bool,
        confirmation_phrase: str | None,
        partial_failure: bool,
    ) -> dict[str, Any]:
        cid = self._require_customer_id(customer_id, payload)
        operations = payload.get("operations")
        if operations is None:
            operations = self._operations_for_simple_mutation(spec.name, cid, payload)
        if not operations:
            return self._operation_template(spec)
        return await self.gateway.mutate(
            customer_id=cid,
            operations=operations,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            partial_failure=partial_failure,
            tool_name=spec.name,
            operation_type=spec.name,
        )

    async def _negative_keyword(
        self,
        spec: FriendlyToolSpec,
        *,
        customer_id: str | int | None,
        payload: dict[str, Any],
        filters: dict[str, Any],
        max_rows: int | None,
        page_size: int | None,
        page_token: str | None,
        validate_only: bool,
        execute: bool,
        confirmation_phrase: str | None,
        partial_failure: bool,
    ) -> dict[str, Any]:
        cid = self._require_customer_id(customer_id, payload)
        name = spec.name
        if name.startswith("list_"):
            query = self._negative_keyword_query(name, payload=payload, filters=filters)
            return await self.gateway.search(
                customer_id=cid,
                query=query,
                max_rows=max_rows,
                page_size=page_size,
                page_token=page_token,
            )
        operations = self._negative_keyword_operations(name, cid, payload)
        return await self.gateway.mutate(
            customer_id=cid,
            operations=operations,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            partial_failure=partial_failure,
            tool_name=spec.name,
            operation_type=spec.name,
        )

    async def _service(
        self,
        spec: FriendlyToolSpec,
        *,
        customer_id: str | int | None,
        payload: dict[str, Any],
        validate_only: bool,
        execute: bool,
        confirmation_phrase: str | None,
    ) -> dict[str, Any]:
        default_response = await self._default_service_tool(
            spec,
            customer_id=customer_id,
            payload=payload,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
        )
        if default_response is not None:
            return default_response

        service_name = payload.get("service_name")
        method_name = payload.get("method_name")
        if not service_name or not method_name:
            return {
                "tool": spec.name,
                "mode": "service",
                "description": spec.description,
                "required_payload": {
                    "service_name": "GoogleAds service name, e.g. KeywordPlanIdeaService",
                    "method_name": "snake_case method name, e.g. generate_keyword_ideas",
                    "request_type": "Optional protobuf request type override",
                    "request": "Request payload matching the Google Ads protobuf JSON shape",
                },
                "fallback": "Use google_ads_call_service for the same full-service bridge directly.",
            }
        return await self.gateway.call_service(
            service_name=service_name,
            method_name=method_name,
            request_type=payload.get("request_type"),
            payload=payload.get("request", {}),
            is_write=payload.get("is_write"),
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            tool_name=spec.name,
        )

    async def _default_service_tool(
        self,
        spec: FriendlyToolSpec,
        *,
        customer_id: str | int | None,
        payload: dict[str, Any],
        validate_only: bool,
        execute: bool,
        confirmation_phrase: str | None,
    ) -> dict[str, Any] | None:
        name = spec.name
        if name == "get_recommendation_types":
            return {
                "tool": name,
                "recommendation_types": [
                    "KEYWORD",
                    "CAMPAIGN_BUDGET",
                    "TEXT_AD",
                    "TARGET_CPA_OPT_IN",
                    "MAXIMIZE_CONVERSIONS_OPT_IN",
                    "MAXIMIZE_CONVERSION_VALUE_OPT_IN",
                    "CALLOUT_ASSET",
                    "SITELINK_ASSET",
                    "RESPONSIVE_SEARCH_AD",
                    "BROAD_MATCH_KEYWORD",
                    "TARGET_ROAS_OPT_IN",
                ],
                "note": "The exact available recommendation enum set depends on Google Ads API version.",
            }
        if name in {"get_keyword_bid_estimates", "get_ad_preview", "get_ad_diagnosis"}:
            return {
                "error": "unsupported_capability",
                "tool": name,
                "reason": (
                    "Google Ads API does not expose this as a stable one-call friendly method "
                    "in the current client surface. Use execute_gaql_query or google_ads_call_service "
                    "with the exact current service method for your account/version."
                ),
            }

        cid = self._require_customer_id(customer_id, payload)
        payload_max_rows, payload_page_size = self._payload_row_cap(payload)
        if name == "list_linked_accounts":
            return await self.gateway.search(
                customer_id=cid,
                query=(
                    "SELECT product_link.resource_name, product_link.type, product_link.status "
                    "FROM product_link"
                ),
                max_rows=payload_max_rows,
                page_size=payload_page_size,
                primary_field="product_link.resource_name",
            )
        if name == "get_account_budget":
            return await self.gateway.search(
                customer_id=cid,
                query=(
                    "SELECT account_budget.resource_name, account_budget.status, "
                    "account_budget.billing_setup, account_budget.approved_spending_limit_micros, "
                    "account_budget.approved_start_date_time, account_budget.approved_end_date_time "
                    "FROM account_budget"
                ),
                max_rows=payload_max_rows,
                page_size=payload_page_size,
                primary_field="account_budget.resource_name",
            )
        if name == "get_billing_setup":
            return await self.gateway.search(
                customer_id=cid,
                query=(
                    "SELECT billing_setup.resource_name, billing_setup.status, "
                    "billing_setup.payments_account, billing_setup.payments_account_info.payments_account_id, "
                    "billing_setup.payments_account_info.payments_account_name "
                    "FROM billing_setup"
                ),
                max_rows=payload_max_rows,
                page_size=payload_page_size,
                primary_field="billing_setup.resource_name",
            )
        if name == "list_invoices":
            request = {
                "customer_id": cid,
                "billing_setup": self._required_value(payload, "billing_setup"),
                "issue_year": str(payload.get("issue_year", date.today().year)),
                "issue_month": payload.get("issue_month", "JANUARY"),
            }
            return await self.gateway.call_service(
                service_name="InvoiceService",
                method_name="list_invoices",
                request_type="ListInvoicesRequest",
                payload=request,
                is_write=False,
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
            )
        if name == "download_invoice_pdf":
            return {
                "tool": name,
                "mode": "metadata",
                "note": (
                    "Google Ads InvoiceService returns invoice metadata including pdf_url. "
                    "This MCP does not download or store invoice PDFs to avoid committing billing files. "
                    "Call list_invoices and use the returned pdf_url."
                ),
            }
        if name == "get_keyword_ideas":
            request = self._keyword_ideas_request(cid, payload)
            return await self.gateway.call_service(
                service_name="KeywordPlanIdeaService",
                method_name="generate_keyword_ideas",
                request_type="GenerateKeywordIdeasRequest",
                payload=request,
                is_write=False,
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
            )
        if name == "get_reach_forecast":
            return await self.gateway.call_service(
                service_name="ReachPlanService",
                method_name=payload.get("method_name", "generate_reach_forecast"),
                request_type=payload.get("request_type", "GenerateReachForecastRequest"),
                payload=payload.get("request", {"customer_id": cid}),
                is_write=False,
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
            )
        return None

    def _keyword_ideas_request(self, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        keywords = payload.get("keywords", [])
        url = payload.get("url")
        if not keywords and not url:
            raise ValidationError("get_keyword_ideas requires payload.keywords, payload.url, or both.")
        request: dict[str, Any] = {
            "customer_id": customer_id,
            "include_adult_keywords": bool(payload.get("include_adult_keywords", False)),
        }
        if payload.get("language"):
            request["language"] = payload["language"]
        if payload.get("geo_target_constants"):
            request["geo_target_constants"] = payload["geo_target_constants"]
        if keywords and url:
            request["keyword_and_url_seed"] = {"keywords": keywords, "url": url}
        elif keywords:
            request["keyword_seed"] = {"keywords": keywords}
        else:
            request["url_seed"] = {"url": url}
        if payload.get("page_size"):
            request["page_size"] = int(payload["page_size"])
        return request

    def _payload_row_cap(self, payload: dict[str, Any]) -> tuple[int | None, int | None]:
        max_rows = payload.get("max_rows", 1000)
        page_size = payload.get("page_size")
        return (
            None if max_rows is None else int(max_rows),
            None if page_size is None else int(page_size),
        )

    def _unsupported(self, spec: FriendlyToolSpec) -> dict[str, Any]:
        return {
            "error": "unsupported_capability",
            "tool": spec.name,
            "reason": spec.notes,
            "fallback": "Use google_ads_call_service if your account and the current API version expose an equivalent service method.",
        }

    def _build_query(
        self,
        spec: FriendlyToolSpec,
        *,
        payload: dict[str, Any],
        clauses: list[str],
    ) -> str:
        if not spec.resource:
            raise ValidationError(f"{spec.name} does not have a GAQL resource mapping.")
        clauses = list(clauses)
        identifier = payload.get("id") or payload.get("resource_id")
        resource_name = payload.get("resource_name")
        if identifier and spec.primary_field:
            clauses.append(f"{spec.primary_field} = {self._literal(identifier)}")
        if resource_name:
            clauses.append(f"{spec.resource}.resource_name = {self._literal(resource_name)}")
        query = f"{select_clause(spec.fields)} FROM {spec.resource}"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        return query

    def _filter_clauses(self, filters: dict[str, Any]) -> list[str]:
        return build_filter_clauses(filters)

    async def _filter_clauses_for_resource(
        self,
        resource: str | None,
        filters: dict[str, Any],
        warnings: list[str],
    ) -> list[str]:
        if not filters or not resource or not hasattr(self.gateway, "get_resource_metadata"):
            return self._filter_clauses(filters)
        metadata = await self.gateway.get_resource_metadata(resource)
        if not metadata.get("ok"):
            warnings.append("Filter metadata unavailable; used simple filter validation.")
            return self._filter_clauses(filters)
        return build_filter_clauses(filters, metadata=metadata, warnings=warnings)

    def _attach_warnings(self, result: dict[str, Any], warnings: list[str]) -> None:
        if warnings:
            result["warnings"] = [*result.get("warnings", []), *warnings]

    async def _mcc_hierarchy(
        self,
        *,
        root_customer_id: str,
        payload: dict[str, Any],
        max_accounts: int | None,
        page_size: int | None,
        page_token: str | None,
    ) -> dict[str, Any]:
        max_depth = int(payload.get("max_depth", 10))
        effective_max_accounts = max_accounts if max_accounts is not None else page_size
        if effective_max_accounts is not None:
            effective_max_accounts = int(effective_max_accounts)
            if effective_max_accounts < 1:
                raise ValidationError("max_accounts must be at least 1.")
        pagination_deprecated = page_size is not None and max_accounts is None
        truncated = False
        seen: set[str] = set()
        rows: list[dict[str, Any]] = []

        def cap_reached() -> bool:
            return effective_max_accounts is not None and len(rows) >= effective_max_accounts

        async def visit(customer_id: str, depth: int) -> dict[str, Any]:
            nonlocal truncated
            seen.add(customer_id)
            node: dict[str, Any] = {"id": customer_id, "manager": True, "children": []}
            query = (
                "SELECT customer_client.id, customer_client.descriptive_name, "
                "customer_client.manager, customer_client.level, customer_client.status, "
                "customer_client.client_customer "
                "FROM customer_client "
                "WHERE customer_client.level <= 1"
            )
            current_page_token = page_token if depth == 0 else None
            while True:
                result = await self.gateway.search(
                    customer_id=customer_id,
                    query=query,
                    max_rows=None,
                    page_token=current_page_token,
                    primary_field="customer_client.id",
                )
                for row in result.get("rows", []):
                    if cap_reached():
                        truncated = True
                        break
                    client = row.get("customer_client", {})
                    child_id = str(client.get("id", "")).replace("-", "")
                    if not child_id or child_id == customer_id:
                        if child_id == customer_id:
                            node.update(
                                {
                                    "name": client.get("descriptive_name"),
                                    "manager": client.get("manager", True),
                                    "status": client.get("status"),
                                    "resource_name": client.get("client_customer"),
                                }
                            )
                        continue
                    row_with_parent = {**row, "parent_customer_id": customer_id}
                    rows.append(row_with_parent)
                    child = {
                        "id": child_id,
                        "name": client.get("descriptive_name"),
                        "manager": client.get("manager"),
                        "status": client.get("status"),
                        "resource_name": client.get("client_customer"),
                        "children": [],
                    }
                    if (
                        client.get("manager")
                        and child_id not in seen
                        and depth < max_depth
                        and not cap_reached()
                    ):
                        child = await visit(child_id, depth + 1)
                        child.setdefault("id", child_id)
                        child.setdefault("name", client.get("descriptive_name"))
                        child.setdefault("manager", client.get("manager"))
                        child.setdefault("status", client.get("status"))
                        child.setdefault("resource_name", client.get("client_customer"))
                    node["children"].append(child)
                    if cap_reached():
                        truncated = True
                        break
                next_page_token = result.get("pagination", {}).get("next_page_token")
                if truncated or not next_page_token or next_page_token == current_page_token:
                    break
                current_page_token = next_page_token
            return node

        tree = await visit(root_customer_id, 0)
        return {
            "customer_id": root_customer_id,
            "rows": rows,
            "tree": tree,
            "row_count": len(rows),
            "truncated": truncated,
            "effective_max_accounts": effective_max_accounts,
            "truncation_reason": "max_accounts" if truncated else None,
            "pagination_deprecated": pagination_deprecated,
            "note": "Hierarchy is built recursively by querying each manager account as parent context.",
        }

    def _negative_keyword_query(
        self,
        name: str,
        *,
        payload: dict[str, Any],
        filters: dict[str, Any],
    ) -> str:
        clauses = self._filter_clauses(filters)
        if name == "list_negative_keywords_ad_group":
            fields = (
                "ad_group_criterion.criterion_id",
                "ad_group_criterion.keyword.text",
                "ad_group_criterion.keyword.match_type",
                "ad_group.id",
                "campaign.id",
            )
            clauses.append("ad_group_criterion.negative = TRUE")
            if payload.get("ad_group_id"):
                clauses.append(f"ad_group.id = {self._literal(payload['ad_group_id'])}")
            return f"{select_clause(fields)} FROM ad_group_criterion WHERE " + " AND ".join(clauses)
        if name == "list_negative_keywords_campaign":
            fields = (
                "campaign_criterion.criterion_id",
                "campaign_criterion.keyword.text",
                "campaign_criterion.keyword.match_type",
                "campaign.id",
            )
            clauses.append("campaign_criterion.negative = TRUE")
            if payload.get("campaign_id"):
                clauses.append(f"campaign.id = {self._literal(payload['campaign_id'])}")
            return f"{select_clause(fields)} FROM campaign_criterion WHERE " + " AND ".join(clauses)
        fields = ("shared_set.id", "shared_set.name", "shared_set.type", "shared_set.status")
        clauses.append("shared_set.type = NEGATIVE_KEYWORDS")
        return f"{select_clause(fields)} FROM shared_set WHERE " + " AND ".join(clauses)

    def _negative_keyword_operations(
        self,
        name: str,
        customer_id: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if name == "add_negative_keywords_ad_group":
            ad_group_id = self._required_id(payload, "ad_group_id")
            return [
                {
                    "ad_group_criterion_operation": {
                        "create": {
                            "ad_group": f"customers/{customer_id}/adGroups/{ad_group_id}",
                            "negative": True,
                            "keyword": {
                                "text": item["text"],
                                "match_type": item.get("match_type", "PHRASE"),
                            },
                        }
                    }
                }
                for item in self._keyword_items(payload)
            ]
        if name == "add_negative_keywords_campaign":
            campaign_id = self._required_id(payload, "campaign_id")
            return [
                {
                    "campaign_criterion_operation": {
                        "create": {
                            "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
                            "negative": True,
                            "keyword": {
                                "text": item["text"],
                                "match_type": item.get("match_type", "PHRASE"),
                            },
                        }
                    }
                }
                for item in self._keyword_items(payload)
            ]
        if name == "remove_negative_keywords_ad_group":
            ad_group_id = self._required_id(payload, "ad_group_id")
            return [
                {
                    "ad_group_criterion_operation": {
                        "remove": f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}"
                    }
                }
                for criterion_id in self._ids(payload, "criterion_ids")
            ]
        if name == "remove_negative_keywords_campaign":
            campaign_id = self._required_id(payload, "campaign_id")
            return [
                {
                    "campaign_criterion_operation": {
                        "remove": f"customers/{customer_id}/campaignCriteria/{campaign_id}~{criterion_id}"
                    }
                }
                for criterion_id in self._ids(payload, "criterion_ids")
            ]
        if name == "create_shared_negative_keyword_list":
            list_name = self._required_value(payload, "name")
            return [
                {
                    "shared_set_operation": {
                        "create": {"name": list_name, "type": "NEGATIVE_KEYWORDS"}
                    }
                }
            ]
        if name == "add_keywords_to_shared_list":
            shared_set_id = self._required_id(payload, "shared_set_id")
            return [
                {
                    "shared_criterion_operation": {
                        "create": {
                            "shared_set": f"customers/{customer_id}/sharedSets/{shared_set_id}",
                            "keyword": {
                                "text": item["text"],
                                "match_type": item.get("match_type", "PHRASE"),
                            },
                        }
                    }
                }
                for item in self._keyword_items(payload)
            ]
        if name == "remove_keywords_from_shared_list":
            return [
                {
                    "shared_criterion_operation": {
                        "remove": f"customers/{customer_id}/sharedCriteria/{criterion_id}"
                    }
                }
                for criterion_id in self._ids(payload, "criterion_ids")
            ]
        if name == "apply_shared_list_to_campaign":
            campaign_id = self._required_id(payload, "campaign_id")
            shared_set_id = self._required_id(payload, "shared_set_id")
            return [
                {
                    "campaign_shared_set_operation": {
                        "create": {
                            "campaign": f"customers/{customer_id}/campaigns/{campaign_id}",
                            "shared_set": f"customers/{customer_id}/sharedSets/{shared_set_id}",
                        }
                    }
                }
            ]
        if name == "remove_shared_list_from_campaign":
            campaign_shared_set_id = self._required_id(payload, "campaign_shared_set_id")
            return [
                {
                    "campaign_shared_set_operation": {
                        "remove": f"customers/{customer_id}/campaignSharedSets/{campaign_shared_set_id}"
                    }
                }
            ]
        if name == "bulk_add_negative_keywords":
            level = payload.get("level", "campaign")
            if level == "ad_group":
                return self._negative_keyword_operations(
                    "add_negative_keywords_ad_group", customer_id, payload
                )
            if level == "campaign":
                return self._negative_keyword_operations(
                    "add_negative_keywords_campaign", customer_id, payload
                )
            raise ValidationError("payload.level must be 'campaign' or 'ad_group'.")
        raise ValidationError(f"{name} is not a recognized negative keyword helper.")

    def _operations_for_simple_mutation(
        self,
        name: str,
        customer_id: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if name == "batch_mutate":
            return payload.get("operations", [])
        if name in CAMPAIGN_CREATE_TOOLS:
            return self._create_campaign_operations(name, customer_id, payload)
        if name in BUDGET_CREATE_TOOLS:
            return [
                self._create_budget_operation(
                    payload,
                    explicitly_shared=name == "create_shared_budget",
                    require_explicit=True,
                )
            ]
        if name in BUDGET_UPDATE_TOOLS:
            return [self._update_budget_operation(customer_id, payload)]
        if name == "remove_budget":
            return [
                {
                    "campaign_budget_operation": {
                        "remove": f"customers/{customer_id}/campaignBudgets/{self._required_id(payload, 'budget_id')}"
                    }
                }
            ]
        if name == "link_budget_to_campaign":
            return [
                self._campaign_update_operation(
                    customer_id,
                    self._required_id(payload, "campaign_id"),
                    {
                        "campaign_budget": self._resource_name(
                            customer_id, "campaignBudgets", self._required_id(payload, "budget_id")
                        )
                    },
                    ["campaign_budget"],
                )
            ]
        if name == "update_campaign":
            campaign_id = self._required_id(payload, "campaign_id")
            updates = {
                key: value
                for key, value in {
                    "name": payload.get("name"),
                    "status": payload.get("status"),
                    "start_date": payload.get("start_date"),
                    "end_date": payload.get("end_date"),
                    "tracking_url_template": payload.get("tracking_template"),
                    "final_url_suffix": payload.get("final_url_suffix"),
                }.items()
                if value is not None
            }
            return [self._campaign_update_operation(customer_id, campaign_id, updates, list(updates))]
        if name == "update_network_settings":
            campaign_id = self._required_id(payload, "campaign_id")
            return [
                self._campaign_update_operation(
                    customer_id,
                    campaign_id,
                    {
                        "network_settings": {
                            "target_google_search": payload.get("target_google_search", True),
                            "target_search_network": payload.get("target_search_network", False),
                            "target_content_network": payload.get("target_content_network", False),
                            "target_partner_search_network": payload.get(
                                "target_partner_search_network", False
                            ),
                        }
                    },
                    ["network_settings"],
                )
            ]
        if name in CAMPAIGN_BULK_STATUS_TOOLS:
            status = "PAUSED" if name == "bulk_pause_campaigns" else "ENABLED"
            return [
                self._status_operation("campaign", customer_id, item, status)
                for item in self._campaign_ids(payload)
            ]
        if name in CAMPAIGN_STATUS_TOOLS:
            status = "PAUSED" if name == "pause_campaign" else "ENABLED"
            return [
                self._status_operation(
                    "campaign", customer_id, self._required_id(payload, "campaign_id"), status
                )
            ]
        if name == "remove_campaign":
            return [
                self._remove_operation("campaign", customer_id, self._required_id(payload, "campaign_id"))
            ]
        if name == "create_ad_group":
            return [self._create_ad_group_operation(customer_id, payload)]
        if name == "update_ad_group":
            return [self._update_ad_group_operation(customer_id, payload)]
        if name in AD_GROUP_STATUS_TOOLS:
            status = "PAUSED" if name == "pause_ad_group" else "ENABLED"
            return [
                self._status_operation("ad_group", customer_id, self._required_id(payload, "ad_group_id"), status)
            ]
        if name == "remove_ad_group":
            return [
                self._remove_operation("ad_group", customer_id, self._required_id(payload, "ad_group_id"))
            ]
        if name == "create_responsive_search_ad":
            return [self._create_responsive_search_ad_operation(customer_id, payload)]
        if name in AD_STATUS_TOOLS:
            status = "PAUSED" if name == "pause_ad" else "ENABLED"
            return [self._ad_status_operation(customer_id, payload, status)]
        if name == "remove_ad":
            return [
                {
                    "ad_group_ad_operation": {
                        "remove": self._ad_group_ad_resource_name(customer_id, payload)
                    }
                }
            ]
        if name in KEYWORD_CREATE_TOOLS:
            ad_group_id = self._required_id(payload, "ad_group_id")
            return [
                {
                    "ad_group_criterion_operation": {
                        "create": {
                            "ad_group": f"customers/{customer_id}/adGroups/{ad_group_id}",
                            "status": item.get("status", "ENABLED"),
                            "keyword": {
                                "text": item["text"],
                                "match_type": item.get("match_type", "EXACT"),
                            },
                        }
                    }
                }
                for item in self._keyword_items(payload)
            ]
        if name in KEYWORD_BID_TOOLS:
            return self._keyword_bid_operations(customer_id, payload)
        if name in KEYWORD_STATUS_TOOLS:
            status = "PAUSED" if name == "pause_keyword" else "ENABLED"
            return self._keyword_status_operations(customer_id, payload, status)
        if name == "remove_keywords":
            return [
                {
                    "ad_group_criterion_operation": {
                        "remove": f"customers/{customer_id}/adGroupCriteria/{self._required_id(payload, 'ad_group_id')}~{criterion_id}"
                    }
                }
                for criterion_id in self._ids(payload, "criterion_ids")
            ]
        if name in ASSET_MUTATION_TOOLS:
            return [self._create_asset_operation(name, payload)]
        if name in {"create_label", "update_label", "remove_label"}:
            return [self._label_operation(name, customer_id, payload)]
        if name in APPLY_LABEL_TOOLS:
            return self._apply_label_operations(name, customer_id, payload)
        if name in REMOVE_LABEL_FROM_TOOLS:
            return self._remove_label_operations(name, customer_id, payload)
        return []

    def _create_campaign_operations(
        self,
        name: str,
        customer_id: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        channel_map = CAMPAIGN_CHANNEL_BY_CREATE_TOOL
        temp_budget_resource = self._resource_name(customer_id, "campaignBudgets", "-1")
        campaign_budget = payload.get("campaign_budget_resource_name")
        if not campaign_budget:
            budget_id = payload.get("budget_id")
            campaign_budget = (
                self._resource_name(customer_id, "campaignBudgets", budget_id)
                if budget_id
                else temp_budget_resource
            )
        operations: list[dict[str, Any]] = []
        if campaign_budget == temp_budget_resource:
            operations.append(
                self._create_budget_operation(
                    payload,
                    explicitly_shared=False,
                    resource_name=temp_budget_resource,
                )
            )

        campaign: dict[str, Any] = {
            "name": self._required_value(payload, "name"),
            "status": payload.get("status", "PAUSED"),
            "advertising_channel_type": channel_map[name],
            "campaign_budget": campaign_budget,
            "contains_eu_political_advertising": payload.get(
                "contains_eu_political_advertising",
                "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING",
            ),
        }
        if payload.get("start_date"):
            campaign["start_date"] = payload["start_date"]
        if payload.get("end_date"):
            campaign["end_date"] = payload["end_date"]
        if payload.get("tracking_template"):
            campaign["tracking_url_template"] = payload["tracking_template"]
        if payload.get("final_url_suffix"):
            campaign["final_url_suffix"] = payload["final_url_suffix"]
        if name == "create_app_campaign":
            campaign["advertising_channel_sub_type"] = payload.get(
                "advertising_channel_sub_type",
                "APP_CAMPAIGN",
            )
            campaign["app_campaign_setting"] = {
                "app_id": self._required_value(payload, "app_id"),
                "app_store": payload.get("app_store", "GOOGLE_APP_STORE"),
                "bidding_strategy_goal_type": payload.get(
                    "app_bidding_strategy_goal_type",
                    payload.get(
                        "bidding_strategy_goal_type",
                        "OPTIMIZE_INSTALLS_WITHOUT_TARGET_INSTALL_COST",
                    ),
                ),
            }
        if name == "create_search_campaign":
            campaign["network_settings"] = {
                "target_google_search": payload.get("target_google_search", True),
                "target_search_network": payload.get("target_search_network", False),
                "target_content_network": payload.get("target_content_network", False),
                "target_partner_search_network": payload.get("target_partner_search_network", False),
            }
        merchant_id = payload.get("merchant_id")
        if name in {"create_shopping_campaign", "create_pmax_campaign"} and merchant_id:
            campaign["shopping_setting"] = {
                "merchant_id": int(str(merchant_id).replace("-", "")),
            }
            if payload.get("feed_label"):
                campaign["shopping_setting"]["feed_label"] = payload["feed_label"]
            if name == "create_shopping_campaign":
                campaign["shopping_setting"]["campaign_priority"] = int(
                    payload.get("campaign_priority", 0)
                )
        campaign.update(self._bidding_payload(payload, channel_type=channel_map[name]))
        pmax_business_name = None
        if name == "create_pmax_campaign" and payload.get("include_business_name_asset", True):
            pmax_business_name = str(
                payload.get("business_name") or payload.get("brand_name") or payload["name"]
            )[:25]
            campaign["resource_name"] = self._resource_name(customer_id, "campaigns", "-2")
        operations.append({"campaign_operation": {"create": campaign}})
        if pmax_business_name:
            asset_resource = self._resource_name(customer_id, "assets", "-3")
            operations.append(
                {
                    "asset_operation": {
                        "create": {
                            "resource_name": asset_resource,
                            "name": payload.get("business_name_asset_name", "MCP PMax business name"),
                            "text_asset": {"text": pmax_business_name},
                        }
                    }
                }
            )
            operations.append(
                {
                    "campaign_asset_operation": {
                        "create": {
                            "campaign": campaign["resource_name"],
                            "asset": asset_resource,
                            "field_type": "BUSINESS_NAME",
                        }
                    }
                }
            )
            logo_asset = payload.get("logo_asset_resource_name")
            if not logo_asset and payload.get("logo_asset_id"):
                logo_asset = self._resource_name(customer_id, "assets", payload["logo_asset_id"])
            if logo_asset:
                operations.append(
                    {
                        "campaign_asset_operation": {
                            "create": {
                                "campaign": campaign["resource_name"],
                                "asset": logo_asset,
                                "field_type": "LOGO",
                            }
                        }
                    }
                )
        return operations

    def _bidding_payload(
        self,
        payload: dict[str, Any],
        *,
        channel_type: str | None = None,
    ) -> dict[str, Any]:
        if payload.get("bidding_strategy"):
            return {"bidding_strategy": payload["bidding_strategy"]}
        default_by_channel = {
            "PERFORMANCE_MAX": "MAXIMIZE_CONVERSION_VALUE",
            "MULTI_CHANNEL": "MAXIMIZE_CONVERSIONS",
            "VIDEO": "MANUAL_CPV",
            "DEMAND_GEN": "MAXIMIZE_CONVERSIONS",
        }
        strategy = payload.get("bidding_strategy_type") or default_by_channel.get(
            channel_type or "",
            "MANUAL_CPC",
        )
        if strategy == "MAXIMIZE_CONVERSIONS":
            return {"maximize_conversions": {}}
        if strategy == "MAXIMIZE_CONVERSION_VALUE":
            return {"maximize_conversion_value": {}}
        if strategy == "TARGET_CPA":
            return {"target_cpa": {"target_cpa_micros": int(payload["target_cpa_micros"])}}
        if strategy == "TARGET_ROAS":
            target_roas = float(payload["target_roas"])
            if not 0.01 <= target_roas <= 1000:
                raise ValidationError(
                    "target_roas must be a ratio, not a percent. Use 4.0 for 400%."
                )
            return {"target_roas": {"target_roas": target_roas}}
        if strategy == "MANUAL_CPM":
            return {"manual_cpm": {}}
        if strategy == "MANUAL_CPV":
            return {"manual_cpv": {}}
        return {"manual_cpc": {"enhanced_cpc_enabled": bool(payload.get("enhanced_cpc_enabled", False))}}

    def _create_budget_operation(
        self,
        payload: dict[str, Any],
        *,
        explicitly_shared: bool | None = None,
        resource_name: str | None = None,
        require_explicit: bool = False,
    ) -> dict[str, Any]:
        budget_name = payload.get("budget_name") or payload.get("name")
        amount_micros = payload.get("amount_micros", payload.get("daily_budget_micros"))
        if require_explicit:
            if not budget_name:
                raise ValidationError("create_budget requires payload.name or payload.budget_name.")
            if amount_micros is None:
                raise ValidationError(
                    "create_budget requires payload.amount_micros or payload.daily_budget_micros."
                )
        budget = {
            "name": budget_name or "MCP budget",
            "amount_micros": int(amount_micros if amount_micros is not None else 1_000_000),
            "delivery_method": payload.get("delivery_method", "STANDARD"),
        }
        if explicitly_shared is not None:
            budget["explicitly_shared"] = explicitly_shared
        if resource_name:
            budget["resource_name"] = resource_name
        return {"campaign_budget_operation": {"create": budget}}

    def _update_budget_operation(self, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        budget_id = self._required_id(payload, "budget_id")
        update = {"resource_name": self._resource_name(customer_id, "campaignBudgets", budget_id)}
        mask = []
        if payload.get("amount_micros") is not None:
            update["amount_micros"] = int(payload["amount_micros"])
            mask.append("amount_micros")
        if payload.get("delivery_method") is not None:
            update["delivery_method"] = payload["delivery_method"]
            mask.append("delivery_method")
        if payload.get("name") is not None:
            update["name"] = payload["name"]
            mask.append("name")
        if not mask:
            raise ValidationError("Budget update requires amount_micros, delivery_method, or name.")
        return {"campaign_budget_operation": {"update": update, "update_mask": self._field_mask(mask)}}

    def _campaign_update_operation(
        self,
        customer_id: str,
        campaign_id: str,
        updates: dict[str, Any],
        mask: list[str],
    ) -> dict[str, Any]:
        if not updates:
            raise ValidationError("Campaign update requires at least one changed field.")
        update = {"resource_name": self._resource_name(customer_id, "campaigns", campaign_id), **updates}
        return {"campaign_operation": {"update": update, "update_mask": self._field_mask(mask)}}

    def _create_ad_group_operation(self, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        campaign = payload.get("campaign_resource_name") or self._resource_name(
            customer_id, "campaigns", self._required_id(payload, "campaign_id")
        )
        ad_group = {
            "name": self._required_value(payload, "name"),
            "campaign": campaign,
            "status": payload.get("status", "ENABLED"),
            "type": payload.get("type", "SEARCH_STANDARD"),
        }
        if payload.get("cpc_bid_micros") is not None:
            ad_group["cpc_bid_micros"] = int(payload["cpc_bid_micros"])
        if payload.get("cpm_bid_micros") is not None:
            ad_group["cpm_bid_micros"] = int(payload["cpm_bid_micros"])
        if payload.get("target_cpa_micros") is not None:
            ad_group["target_cpa_micros"] = int(payload["target_cpa_micros"])
        return {"ad_group_operation": {"create": ad_group}}

    def _update_ad_group_operation(self, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        ad_group_id = self._required_id(payload, "ad_group_id")
        update = {"resource_name": self._resource_name(customer_id, "adGroups", ad_group_id)}
        mask = []
        for field in ("name", "status", "cpc_bid_micros", "cpm_bid_micros", "target_cpa_micros"):
            if payload.get(field) is not None:
                update[field] = payload[field]
                mask.append(field)
        if not mask:
            raise ValidationError("Ad group update requires at least one changed field.")
        return {"ad_group_operation": {"update": update, "update_mask": self._field_mask(mask)}}

    def _create_responsive_search_ad_operation(
        self,
        customer_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        headlines = [{"text": text} if isinstance(text, str) else text for text in payload.get("headlines", [])]
        descriptions = [
            {"text": text} if isinstance(text, str) else text for text in payload.get("descriptions", [])
        ]
        if not headlines or not descriptions:
            raise ValidationError("Responsive search ads require payload.headlines and payload.descriptions.")
        if len(headlines) < 3:
            raise ValidationError("create_responsive_search_ad requires at least 3 headlines.")
        if len(descriptions) < 2:
            raise ValidationError("create_responsive_search_ad requires at least 2 descriptions.")
        ad = {
            "responsive_search_ad": {"headlines": headlines, "descriptions": descriptions},
            "final_urls": payload.get("final_urls", []),
        }
        if not ad["final_urls"]:
            raise ValidationError("Responsive search ads require payload.final_urls.")
        return {
            "ad_group_ad_operation": {
                "create": {
                    "ad_group": self._resource_name(
                        customer_id, "adGroups", self._required_id(payload, "ad_group_id")
                    ),
                    "status": payload.get("status", "PAUSED"),
                    "ad": ad,
                }
            }
        }

    def _ad_status_operation(self, customer_id: str, payload: dict[str, Any], status: str) -> dict[str, Any]:
        return {
            "ad_group_ad_operation": {
                "update": {"resource_name": self._ad_group_ad_resource_name(customer_id, payload), "status": status},
                "update_mask": "status",
            }
        }

    def _keyword_bid_operations(self, customer_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        updates = payload.get("keyword_bids") or [
            {"criterion_id": item, "cpc_bid_micros": payload.get("cpc_bid_micros")}
            for item in self._ids(payload, "criterion_ids")
        ]
        ad_group_id = self._required_id(payload, "ad_group_id")
        operations = []
        for item in updates:
            if item.get("cpc_bid_micros") is None:
                raise ValidationError("Keyword bid updates require cpc_bid_micros.")
            operations.append(
                {
                    "ad_group_criterion_operation": {
                        "update": {
                            "resource_name": f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{item['criterion_id']}",
                            "cpc_bid_micros": int(item["cpc_bid_micros"]),
                        },
                        "update_mask": self._field_mask(["cpc_bid_micros"]),
                    }
                }
            )
        return operations

    def _keyword_status_operations(
        self,
        customer_id: str,
        payload: dict[str, Any],
        status: str,
    ) -> list[dict[str, Any]]:
        ad_group_id = self._required_id(payload, "ad_group_id")
        return [
            {
                "ad_group_criterion_operation": {
                    "update": {
                        "resource_name": f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}",
                        "status": status,
                    },
                    "update_mask": "status",
                }
            }
            for criterion_id in self._ids(payload, "criterion_ids")
        ]

    def _create_asset_operation(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        asset: dict[str, Any] = {"name": payload.get("name", "MCP asset")}
        if name == "create_sitelink":
            asset["sitelink_asset"] = {
                "link_text": self._required_value(payload, "link_text"),
                "description1": payload.get("description1", ""),
                "description2": payload.get("description2", ""),
            }
            asset["final_urls"] = payload.get("final_urls", [])
        elif name == "create_callout":
            asset["callout_asset"] = {"callout_text": self._required_value(payload, "callout_text")}
        elif name == "create_text_asset":
            asset["text_asset"] = {"text": self._required_value(payload, "text")}
        elif name == "create_video_asset":
            asset["youtube_video_asset"] = {
                "youtube_video_id": self._required_value(payload, "youtube_video_id")
            }
        return {"asset_operation": {"create": asset}}

    def _label_operation(self, name: str, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if name == "create_label":
            return {
                "label_operation": {
                    "create": {
                        "name": self._required_value(payload, "name"),
                        "text_label": {"background_color": payload.get("background_color", "#4285F4")},
                    }
                }
            }
        label_id = self._required_id(payload, "label_id")
        if name == "remove_label":
            return {"label_operation": {"remove": self._resource_name(customer_id, "labels", label_id)}}
        update = {"resource_name": self._resource_name(customer_id, "labels", label_id)}
        mask = []
        if payload.get("name"):
            update["name"] = payload["name"]
            mask.append("name")
        if payload.get("background_color"):
            update["text_label"] = {"background_color": payload["background_color"]}
            mask.append("text_label.background_color")
        if not mask:
            raise ValidationError("Label update requires name or background_color.")
        return {"label_operation": {"update": update, "update_mask": self._field_mask(mask)}}

    def _status_operation(
        self,
        entity: str,
        customer_id: str,
        entity_id: str | int,
        status: str,
    ) -> dict[str, Any]:
        resource = {
            "campaign": ("campaign_operation", "campaigns"),
            "ad_group": ("ad_group_operation", "adGroups"),
        }[entity]
        op_name, resource_collection = resource
        return {
            op_name: {
                "update": {
                    "resource_name": f"customers/{customer_id}/{resource_collection}/{entity_id}",
                    "status": status,
                },
                "update_mask": "status",
            }
        }

    def _remove_operation(self, entity: str, customer_id: str, entity_id: str | int) -> dict[str, Any]:
        op_name, resource_collection = {
            "campaign": ("campaign_operation", "campaigns"),
            "ad_group": ("ad_group_operation", "adGroups"),
        }[entity]
        return {op_name: {"remove": f"customers/{customer_id}/{resource_collection}/{entity_id}"}}

    def _apply_label_operations(
        self,
        name: str,
        customer_id: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        label_id = self._required_id(payload, "label_id")
        label = self._resource_name(customer_id, "labels", label_id)
        if "campaign" in name:
            return [
                {
                    "campaign_label_operation": {
                        "create": {
                            "campaign": self._resource_name(customer_id, "campaigns", item),
                            "label": label,
                        }
                    }
                }
                for item in self._ids(payload, "campaign_ids")
            ]
        if "ad_group" in name:
            return [
                {
                    "ad_group_label_operation": {
                        "create": {
                            "ad_group": self._resource_name(customer_id, "adGroups", item),
                            "label": label,
                        }
                    }
                }
                for item in self._ids(payload, "ad_group_ids")
            ]
        if "keyword" in name:
            ad_group_id = self._required_id(payload, "ad_group_id")
            return [
                {
                    "ad_group_criterion_label_operation": {
                        "create": {
                            "ad_group_criterion": f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}",
                            "label": label,
                        }
                    }
                }
                for criterion_id in self._ids(payload, "criterion_ids")
            ]
        if "ad" in name:
            return [
                {
                    "ad_group_ad_label_operation": {
                        "create": {
                            "ad_group_ad": self._ad_group_ad_resource_name(customer_id, item),
                            "label": label,
                        }
                    }
                }
                for item in payload.get("ads", [payload])
            ]
        raise ValidationError(f"{name} does not have a label apply implementation.")

    def _remove_label_operations(
        self,
        name: str,
        customer_id: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        label_id = self._required_id(payload, "label_id")
        if "campaign" in name:
            return [
                {
                    "campaign_label_operation": {
                        "remove": f"customers/{customer_id}/campaignLabels/{campaign_id}~{label_id}"
                    }
                }
                for campaign_id in self._ids(payload, "campaign_ids")
            ]
        if "ad_group" in name:
            return [
                {
                    "ad_group_label_operation": {
                        "remove": f"customers/{customer_id}/adGroupLabels/{ad_group_id}~{label_id}"
                    }
                }
                for ad_group_id in self._ids(payload, "ad_group_ids")
            ]
        if "keyword" in name:
            ad_group_id = self._required_id(payload, "ad_group_id")
            return [
                {
                    "ad_group_criterion_label_operation": {
                        "remove": f"customers/{customer_id}/adGroupCriterionLabels/{ad_group_id}~{criterion_id}~{label_id}"
                    }
                }
                for criterion_id in self._ids(payload, "criterion_ids")
            ]
        if "ad" in name:
            return [
                {
                    "ad_group_ad_label_operation": {
                        "remove": (
                            f"customers/{customer_id}/adGroupAdLabels/"
                            f"{self._required_id(item, 'ad_group_id')}~{self._required_id(item, 'ad_id')}~{label_id}"
                        )
                    }
                }
                for item in payload.get("ads", [payload])
            ]
        raise ValidationError(f"{name} does not have a label remove implementation.")

    def _operation_template(self, spec: FriendlyToolSpec) -> dict[str, Any]:
        return {
            "tool": spec.name,
            "mode": "mutate",
            "description": spec.description,
            "required_payload": {
                "operations": [
                    "List of GoogleAdsService MutateOperation payloads in protobuf JSON shape."
                ]
            },
            "write_safety": {
                "default": "validate_only=true",
                "real_write_requires": {
                    "execute": True,
                    "confirmation_phrase": CONFIRMATION_PHRASE,
                },
            },
            "examples": {
                "campaign_status_update": {
                    "campaign_operation": {
                        "update": {
                            "resource_name": "customers/1234567890/campaigns/111",
                            "status": "PAUSED",
                        },
                        "update_mask": "status",
                    }
                }
            },
        }

    def _keyword_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items = payload.get("keywords")
        if not items:
            raise ValidationError("payload.keywords is required.")
        normalized = []
        for item in items:
            if isinstance(item, str):
                normalized.append({"text": item})
            else:
                text = item.get("text")
                if not text:
                    raise ValidationError("Each keyword item requires text.")
                normalized.append(dict(item))
        return normalized

    def _ids(self, payload: dict[str, Any], field: str = "ids") -> list[str]:
        ids = payload.get(field)
        if ids is None and field != "ids":
            ids = payload.get("ids")
        if not ids:
            raise ValidationError(f"payload.{field} is required.")
        return [str(item).replace("-", "") for item in ids]

    def _campaign_ids(self, payload: dict[str, Any]) -> list[str]:
        ids = payload.get("campaign_ids")
        if ids is None:
            ids = payload.get("ids")
        if not ids:
            raise ValidationError("payload.campaign_ids is required.")
        return [str(item).replace("-", "") for item in ids]

    def _validate_change_event_range(
        self,
        date_range: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> None:
        if start_date or end_date:
            if not start_date or not end_date:
                return
            start = date.fromisoformat(validate_date(start_date, "start_date"))
            end = date.fromisoformat(validate_date(end_date, "end_date"))
            if (end - start).days > 30:
                raise ValidationError("change_event supports a maximum 30-day lookback.")
            if start < date.today() - timedelta(days=30):
                raise ValidationError("change_event custom ranges must start within the last 30 days.")
            return
        allowed = {"TODAY", "YESTERDAY", "LAST_7_DAYS", "LAST_14_DAYS", "LAST_30_DAYS"}
        selected = (date_range or CHANGE_EVENT_DEFAULT_DATE_RANGE).upper()
        if selected not in allowed:
            raise ValidationError("change_event supports only up to LAST_30_DAYS.")

    def _effective_report_date_range(
        self,
        spec: FriendlyToolSpec,
        *,
        date_range: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> str | None:
        if start_date or end_date:
            return date_range
        if date_range:
            return date_range
        if spec.resource == "change_event":
            return CHANGE_EVENT_DEFAULT_DATE_RANGE
        return DEFAULT_REPORT_DATE_RANGE

    def _report_date_field(self, resource: str | None) -> str:
        if resource == "change_event":
            return "change_event.change_date_time"
        if resource == "call_view":
            return "call_view.start_call_date_time"
        return "segments.date"

    def _required_value(self, payload: dict[str, Any], field: str) -> str:
        value = payload.get(field)
        if value is None or value == "":
            raise ValidationError(f"payload.{field} is required.")
        return str(value)

    def _required_id(self, payload: dict[str, Any], field: str) -> str:
        return self._required_value(payload, field).replace("-", "")

    def _required(self, payload: dict[str, Any], field: str) -> str:
        return self._required_value(payload, field)

    def _require_customer_id(
        self,
        customer_id: str | int | None,
        payload: dict[str, Any],
    ) -> str:
        value = customer_id or payload.get("customer_id")
        if not value:
            raise ValidationError("customer_id is required.")
        return normalize_customer_id(value)

    def _resource_name(self, customer_id: str, collection: str, entity_id: str | int) -> str:
        raw = str(entity_id).strip()
        normalized = raw if raw.startswith("-") else raw.replace("-", "")
        return f"customers/{customer_id}/{collection}/{normalized}"

    def _ad_group_ad_resource_name(
        self,
        customer_id: str,
        payload: dict[str, Any],
    ) -> str:
        if payload.get("resource_name"):
            return payload["resource_name"]
        ad_group_id = self._required_id(payload, "ad_group_id")
        ad_id = self._required_id(payload, "ad_id")
        return f"customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}"

    def _literal(self, value: Any) -> str:
        return gaql_literal(value)

    def _field_mask(self, paths: list[str]) -> str:
        return ",".join(self._json_field_path(path) for path in paths)

    def _json_field_path(self, path: str) -> str:
        return ".".join(self._lower_camel(part) for part in path.split("."))

    def _lower_camel(self, value: str) -> str:
        parts = value.split("_")
        return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])
