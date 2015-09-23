from string import Formatter
from pygments.token import Token, string_to_tokentype
from prompt_toolkit.styles import DefaultStyle
from prompt_toolkit.layout.controls import UIControl
import tmuxp
import os

scap_styles = {
    Token: '#dddddd',
    Token.Text: '#f6f6f6',
    Token.Prompt: '#dddddd',
    Token.Env: '#aaccff',
    Token.Attr: '#6699bb',
    Token.Toolbar: '#9999ff bg:#333333',
    Token.Toolbar.Text: '#999999',
    Token.Toolbar.Value: '#aaccff',
    Token.Name.Variable: "#aaccff",
}

class ScapStyle(DefaultStyle):
    styles = {}
    styles.update(scap_styles)
    styles.update(DefaultStyle.styles)

def get_prompt_tokens(context):
    return tokenize_string("# {project_name@Attr}{rcwd@Env} > ", context,
                            text_token=Token.Prompt)

def get_toolbar_tokens(context):
    return tokenize_string("User: {u} | {project_name:Project} | cwd: {project_root@Attr}{rcwd@Env} | {cmd:Last Command}", context,
                            Token.Toolbar.Text,
                            Token.Toolbar.Value)


class TerminalControl(UIControl):
    """
    a prompt_toolkit UIControl that uses pexpect's terminal emulator
    """
    def __init__(self):
        self.character = ' '
        self.token = Token
        self.term = pexpect.ANSI.ANSI(r=24, c=80)

    def __repr__(self):
        return '%s(character=%r, token=%r)' % (
            self.__class__.__name__, self.character, self.token)

    def reset(self):
        pass

    def has_focus(self, cli):
        return False

    def create_screen(self, cli, width, height):
        char = Char(' ', self.token)
        screen = Screen(width, char)
        screen.write_data(str(self.term), width)
        screen.current_height = height
        return screen


def tokenize_string(text, values,
                    text_token=Token.Text,
                    value_token=Token.Value):
    fmt = Formatter()
    tokens = []
    parsed = fmt.parse(text)
    for x in parsed:
        part,key,lbl,_ = x
        #print x
        try:
            if len(part):
                # static text that appears before the dynamic value:
                tokens.append((text_token, part))

            if '@' in key:
                # @Style in the format string overrides the style token used
                # for this ui element
                key, _, style = key.partition('@')
                vt = string_to_tokentype(style)
            else:
                # use default (or caller-provided) style token
                vt = value_token

            # look up the dynamic value:
            val = str(values[key])
            if (len(val)):
                # if there is a label, display it first
                if (len(lbl)):
                    tokens.append((text_token, str(lbl)+": "))
                # finally display the dynamic value
                tokens.append((vt, val))
        except:
            continue
    return tokens

def setup_tmux():
    if not 'TMUX' in os.environ:
        tmux = tmuxp.Server();
        if tmux.has_session('iscap'):
            print ('error: iscap session already running. Try reattaching with `tmux attach`')
            session = tmux.list_sessions()[0]
            session.attach_session()
            exit(1)
        else:
            session = tmux.new_session(session_name="iscap")
            top_pane = session.attached_pane()
            tmux.cmd('split-window')
            new_pane = session.attached_pane()
            new_pane.clear()
            top_pane.select_pane()
            top_pane.clear()
            top_pane.send_keys('iscap')
            session.attach_session()
            exit(0)

    tmux = tmuxp.Server();
    return tmux