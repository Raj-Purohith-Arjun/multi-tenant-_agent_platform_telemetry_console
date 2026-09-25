from typing import ClassVar

from contracts import Tool
from pydantic import BaseModel, ConfigDict


class EchoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


class EchoOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


class EchoTool:
    name: ClassVar[str] = "echo"
    description: ClassVar[str] = "Returns its input."
    InputModel: ClassVar[type[EchoInput]] = EchoInput
    OutputModel: ClassVar[type[EchoOutput]] = EchoOutput
    side_effecting: ClassVar[bool] = False

    async def run(self, args: EchoInput) -> EchoOutput:
        return EchoOutput(text=args.text)


class NotATool:
    name = "broken"


def test_conforming_class_satisfies_tool_protocol() -> None:
    tool: Tool[EchoInput, EchoOutput] = EchoTool()
    assert isinstance(tool, Tool)


def test_nonconforming_class_does_not_satisfy_tool_protocol() -> None:
    assert not isinstance(NotATool(), Tool)


async def test_tool_run_is_async_and_typed() -> None:
    tool = EchoTool()
    args = tool.InputModel.model_validate({"text": "hi"})
    result = await tool.run(args)
    assert tool.OutputModel.model_validate(result.model_dump()) == EchoOutput(text="hi")
