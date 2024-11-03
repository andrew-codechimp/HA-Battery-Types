"""Repairs for battery_notes."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import data_entry_flow
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir


class MissingDeviceRepairFlow(RepairsFlow):
    """Handler for an issue fixing flow."""

    def __init__(self, data: dict[str, str]) -> None:
        """Initialize."""
        self.entry_id = data["entry_id"]
        self.device_id = data["device_id"]
        self.source_entity_id = data["source_entity_id"]
        self.device_name = data["name"]

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the first step of a fix flow."""

        return await (self.async_step_confirm())

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle the confirm step of a fix flow."""
        if user_input is not None:

            device_registry = dr.async_get(self.hass)
            device_registry.async_remove_device(self.device_id)

            return self.async_create_entry(title="", data={})

        issue_registry = ir.async_get(self.hass)
        description_placeholders = None
        if issue := issue_registry.async_get_issue(self.handler, self.issue_id):
            description_placeholders = issue.translation_placeholders

        return self.async_show_form(
            step_id="confirm_delete_entity",
            data_schema=vol.Schema({}),
            description_placeholders=description_placeholders
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create flow."""
    if issue_id.startswith("missing_device_"):
        assert data
        return MissingDeviceRepairFlow(data)
