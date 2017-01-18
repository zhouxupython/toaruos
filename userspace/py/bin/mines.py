#!/usr/bin/python3
"""
Minesweeper clone
"""
import random
import subprocess
import sys

import cairo

import yutani
import text_region
import toaru_fonts

from button import Button, rounded_rectangle
from menu_bar import MenuBarWidget, MenuEntryAction, MenuEntrySubmenu, MenuEntryDivider, MenuWindow

version = "0.1.0"
_description = f"<b>Mines {version}</b>\n© 2017 Kevin Lange\n\nClassic logic game.\n\n<color 0x0000FF>http://github.com/klange/toaruos</color>"

class MineButton(Button):

    def __init__(self,action,r,c,is_mine,neighbor_mines):
        super(MineButton,self).__init__("",action)
        self.row = r
        self.col = c
        self.tr = text_region.TextRegion(0,0,10,10)
        self.is_mine = is_mine
        self.tr.set_text("")
        self.tr.set_alignment(2)
        self.tr.set_valignment(2)
        self.width = None
        self.revealed = False
        self.mines = neighbor_mines
        self.flagged = False

    def reveal(self):
        if self.revealed: return
        self.revealed = True
        if self.is_mine:
            self.tr.set_text("X")
        elif self.mines == 0:
            self.tr.set_text("")
        else:
            self.tr.set_text(str(self.mines))

    def set_flagged(self):
        self.flagged = not self.flagged

    def draw(self, window, ctx, x, y, w, h):
        if self.width != w:
            self.x, self.y, self.width, self.height = x, y, w, h
            x_, y_ = ctx.user_to_device(x,y)
            self.tr.move(int(x_)+2,int(y_)+2)
            self.tr.resize(w-4,h-4)
        rounded_rectangle(ctx,x+2,y+2,w-4,h-4,3)
        if self.revealed:
            ctx.set_source_rgb(0.6,0.6,0.6)
        elif self.flagged:
            ctx.set_source_rgb(0.6,0.1,0.1)
        elif self.hilight == 1:
            ctx.set_source_rgb(0.7,0.7,0.7)
        elif self.hilight == 2:
            ctx.set_source_rgb(0.3,0.3,0.3)
        else:
            ctx.set_source_rgb(1,1,1)
        ctx.fill()

        if self.tr.text:
            self.tr.draw(window)

class MinesWindow(yutani.Window):

    base_width = 400
    base_height = 440

    def __init__(self, decorator):
        super(MinesWindow, self).__init__(self.base_width + decorator.width(), self.base_height + decorator.height(), title="Mines", icon="mines", doublebuffer=True)
        self.move(100,100)
        self.decorator = decorator

        def new_game(action):
            def mine_func(b):
                button = b
                if self.first_click:
                    while button.is_mine or button.mines:
                        new_game(action)
                        button = self.buttons[button.row][button.col]
                    self.first_click = False
                if button.is_mine:
                    self.tr.set_text("You lose.")
                    for row in self.buttons:
                        for b in row:
                            b.reveal()
                    self.draw()
                    return
                else:
                    if not button.revealed:
                        button.reveal()
                        if button.mines == 0:
                            n = [x for x in check_neighbor_buttons(button.row,button.col) if not x.revealed]
                            while n:
                                b = n.pop()
                                b.reveal()
                                if b.mines == 0:
                                    n.extend([x for x in check_neighbor_buttons(b.row,b.col) if not x.revealed and not x in n])

            self.field_size, self.mine_count = action
            self.first_click = True
            self.tr.set_text(f"There are {self.mine_count} mines.")

            self.mines = []
            while len(self.mines) < self.mine_count:
                x,y = random.randrange(self.field_size),random.randrange(self.field_size)
                if not (x,y) in self.mines:
                    self.mines.append((x,y))

            def check_neighbors(r,c):
                n = []
                if r > 0:
                    if c > 0: n.append((r-1,c-1))
                    n.append((r-1,c))
                    if c < self.field_size-1: n.append((r-1,c+1))
                if r < self.field_size-1:
                    if c > 0: n.append((r+1,c-1))
                    n.append((r+1,c))
                    if c < self.field_size-1: n.append((r+1,c+1))
                if c > 0: n.append((r,c-1))
                if c < self.field_size-1: n.append((r,c+1))
                return n

            def check_neighbor_buttons(r,c):
                return [self.buttons[x][y] for x,y in check_neighbors(r,c)]

            self.buttons = []
            for row in range(self.field_size):
                r = []
                for col in range(self.field_size):
                    is_mine = (row,col) in self.mines
                    neighbor_mines = len([x for x in check_neighbors(row,col) if x in self.mines])
                    r.append(MineButton(mine_func,row,col,is_mine,neighbor_mines))
                self.buttons.append(r)

        def exit_app(action):
            menus = [x for x in self.menus.values()]
            for x in menus:
                x.definitely_close()
            self.close()
            sys.exit(0)
        def about_window(action):
            subprocess.Popen(["about-applet.py","About Mines","mines","/usr/share/icons/48/mines.png",_description])
        def help_browser(action):
            subprocess.Popen(["help-browser.py","mines.trt"])
        menus = [
            ("File", [
                MenuEntrySubmenu("New Game…",[
                    MenuEntryAction("9×9, 10 mines",None,new_game,(9,10)),
                    MenuEntryAction("16×16, 40 mines",None,new_game,(16,40)),
                    MenuEntryAction("20×20, 90 mines",None,new_game,(20,90)),
                ],icon="new"),
                MenuEntryDivider(),
                MenuEntryAction("Exit","exit",exit_app,None),
            ]),
            ("Help", [
                MenuEntryAction("Contents","help",help_browser,None),
                MenuEntryDivider(),
                MenuEntryAction("About Mines","star",about_window,None),
            ]),
        ]

        self.menubar = MenuBarWidget(self,menus)

        self.tr = text_region.TextRegion(self.decorator.left_width()+5,self.decorator.top_height()+self.menubar.height,self.base_width-10,40)
        self.tr.set_font(toaru_fonts.Font(toaru_fonts.FONT_SANS_SERIF,18))
        self.tr.set_alignment(2)
        self.tr.set_valignment(2)
        self.tr.set_one_line()
        self.tr.set_ellipsis()


        self.error = False

        self.hover_widget = None
        self.down_button = None

        self.menus = {}
        self.hovered_menu = None
        self.modifiers = 0

        new_game((9,10))

    def flag(self,button):
        button.set_flagged()
        self.draw()

    def draw(self):
        surface = self.get_cairo_surface()

        WIDTH, HEIGHT = self.width - self.decorator.width(), self.height - self.decorator.height()

        ctx = cairo.Context(surface)
        ctx.translate(self.decorator.left_width(), self.decorator.top_height())
        ctx.rectangle(0,0,WIDTH,HEIGHT)
        ctx.set_source_rgb(204/255,204/255,204/255)
        ctx.fill()

        self.tr.resize(WIDTH-10, self.tr.height)
        self.tr.draw(self)

        offset_x = 0
        offset_y = self.tr.height + self.menubar.height
        button_height = int((HEIGHT - self.tr.height - self.menubar.height) / len(self.buttons))
        for row in self.buttons:
            button_width = int(WIDTH / len(row))
            for button in row:
                if button:
                    button.draw(self,ctx,offset_x,offset_y,button_width,button_height)
                offset_x += button_width
            offset_x = 0
            offset_y += button_height

        self.menubar.draw(ctx,0,0,WIDTH)
        self.decorator.render(self)
        self.flip()

    def finish_resize(self, msg):
        """Accept a resize."""
        if msg.width < 400 or msg.height < 400:
            self.resize_offer(max(msg.width,400),max(msg.height,400))
            return
        self.resize_accept(msg.width, msg.height)
        self.reinit()
        self.draw()
        self.resize_done()
        self.flip()

    def mouse_event(self, msg):
        if d.handle_event(msg) == yutani.Decor.EVENT_CLOSE:
            window.close()
            sys.exit(0)
        x,y = msg.new_x - self.decorator.left_width(), msg.new_y - self.decorator.top_height()
        w,h = self.width - self.decorator.width(), self.height - self.decorator.height()

        if x >= 0 and x < w and y >= 0 and y < self.menubar.height:
            self.menubar.mouse_event(msg, x, y)
            return

        redraw = False
        if self.down_button:
            if msg.command == yutani.MouseEvent.RAISE or msg.command == yutani.MouseEvent.CLICK:
                if not (msg.buttons & yutani.MouseButton.BUTTON_LEFT):
                    if x >= self.down_button.x and \
                        x < self.down_button.x + self.down_button.width and \
                        y >= self.down_button.y and \
                        y < self.down_button.y + self.down_button.height:
                            self.down_button.focus_enter()
                            if self.modifiers & yutani.Modifier.MOD_LEFT_CTRL:
                                self.flag(self.down_button)
                            else:
                                self.down_button.callback(self.down_button)
                            self.down_button = None
                            redraw = True
                    else:
                        self.down_button.focus_leave()
                        self.down_button = None
                        redraw = True

        else:
            if y > self.tr.height + self.menubar.height and y < h and x >= 0 and x < w:
                row = int((y - self.tr.height - self.menubar.height) / (self.height - self.decorator.height() - self.tr.height - self.menubar.height) * len(self.buttons))
                col = int(x / (self.width - self.decorator.width()) * len(self.buttons[row]))
                button = self.buttons[row][col]
                if button != self.hover_widget:
                    if button:
                        button.focus_enter()
                        redraw = True
                    if self.hover_widget:
                        self.hover_widget.focus_leave()
                        redraw = True
                    self.hover_widget = button

                if msg.command == yutani.MouseEvent.DOWN:
                    if button:
                        button.hilight = 2
                        self.down_button = button
                        redraw = True
            else:
                if self.hover_widget:
                    self.hover_widget.focus_leave()
                    redraw = True
                self.hover_widget = None

        if redraw:
            self.draw()

    def keyboard_event(self, msg):
        self.modifiers = msg.event.modifiers
        if msg.event.action != 0x01:
            return # Ignore anything that isn't a key down.
        if msg.event.key == b"q":
            self.close()
            sys.exit(0)

if __name__ == '__main__':
    yutani.Yutani()
    d = yutani.Decor()

    window = MinesWindow(d)
    window.draw()

    while 1:
        # Poll for events.
        msg = yutani.yutani_ctx.poll()
        if msg.type == yutani.Message.MSG_SESSION_END:
            window.close()
            break
        elif msg.type == yutani.Message.MSG_KEY_EVENT:
            if msg.wid == window.wid:
                window.keyboard_event(msg)
            elif msg.wid in window.menus:
                window.menus[msg.wid].keyboard_event(msg)
        elif msg.type == yutani.Message.MSG_WINDOW_FOCUS_CHANGE:
            if msg.wid == window.wid:
                if msg.focused == 0 and window.menus:
                    window.focused = 1
                else:
                    window.focused = msg.focused
                window.draw()
            elif msg.wid in window.menus and msg.focused == 0:
                window.menus[msg.wid].leave_menu()
                if not window.menus and window.focused:
                    window.focused = 0
                    window.draw()
        elif msg.type == yutani.Message.MSG_RESIZE_OFFER:
            if msg.wid == window.wid:
                window.finish_resize(msg)
        elif msg.type == yutani.Message.MSG_WINDOW_MOVE:
            if msg.wid == window.wid:
                window.x = msg.x
                window.y = msg.y
        elif msg.type == yutani.Message.MSG_WINDOW_MOUSE_EVENT:
            if msg.wid == window.wid:
                window.mouse_event(msg)
            elif msg.wid in window.menus:
                m = window.menus[msg.wid]
                if msg.new_x >= 0 and msg.new_x < m.width and msg.new_y >= 0 and msg.new_y < m.height:
                    window.hovered_menu = m
                elif window.hovered_menu == m:
                    window.hovered_menu = None
                m.mouse_action(msg)
