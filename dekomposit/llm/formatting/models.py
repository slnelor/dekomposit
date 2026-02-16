from pydantic import BaseModel, Field
from typing import Any


class FormatPreset(BaseModel):
    """Combined tag + template for formatting output.
    
    Example:
        open_tag: "<translation>"
        close_tag: "</translation>"
        template: "[{source} → {target}] {translation}"
        
        Result: <translation>[EN → RU] Hello</translation>
    """

    name: str = Field(description="Unique preset name")
    description: str = Field(default="", description="User-facing description")
    open_tag: str = Field(description="Opening tag")
    close_tag: str = Field(description="Closing tag")
    template: str = Field(description="Template string with {placeholders}")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    def render(self, **kwargs: Any) -> str:
        """Render the preset with given variables.
        
        Args:
            **kwargs: Variables to fill in template
            
        Returns:
            Formatted string with tags
        """
        content = self.template.format(**kwargs)
        return f"{self.open_tag}{content}{self.close_tag}"

    def validate_template(self) -> bool:
        """Check if template has valid placeholders."""
        return "{" in self.template and "}" in self.template
