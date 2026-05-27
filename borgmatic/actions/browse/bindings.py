import textual.binding
import textual.widgets


OPTION_LIST_BINDINGS = (
    *textual.widgets.OptionList.BINDINGS,
    textual.binding.Binding(
        key='up,k', action='cursor_up', description='scroll up', show=True, priority=True
    ),
    textual.binding.Binding(
        key='down,j', action='cursor_down', description='scroll down', show=True, priority=True
    ),
    textual.binding.Binding(
        key='pageup', action='page_up', description='page up', show=True, priority=True
    ),
    textual.binding.Binding(
        key='pagedown', action='page_down', description='page down', show=True, priority=True
    ),
    textual.binding.Binding(
        key='enter', action='select', description='select', show=True, priority=True
    ),
    textual.binding.Binding(key='right,l', action='select', description='select', show=False),
)
