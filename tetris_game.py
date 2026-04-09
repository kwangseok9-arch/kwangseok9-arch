import random
import tkinter as tk


BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 30
TICK_MS = 450


SHAPES = {
    "I": [(0, 1), (1, 1), (2, 1), (3, 1)],
    "O": [(1, 0), (2, 0), (1, 1), (2, 1)],
    "T": [(1, 0), (0, 1), (1, 1), (2, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}


COLORS = {
    "I": "#38BDF8",
    "O": "#FACC15",
    "T": "#A78BFA",
    "S": "#4ADE80",
    "Z": "#FB7185",
    "J": "#60A5FA",
    "L": "#FB923C",
}


class Tetris:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Tetris")
        self.root.resizable(False, False)

        width_px = BOARD_WIDTH * CELL_SIZE
        height_px = BOARD_HEIGHT * CELL_SIZE

        self.canvas = tk.Canvas(
            root,
            width=width_px,
            height=height_px,
            bg="#0f172a",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, rowspan=2)

        self.info = tk.Label(
            root,
            text="Score: 0\nLines: 0\n\nControls:\n← → Move\n↑ Rotate\n↓ Soft drop\nSpace Hard drop\nR Restart",
            justify="left",
            padx=12,
            pady=12,
            font=("Consolas", 10),
        )
        self.info.grid(row=0, column=1, sticky="n")

        self.status = tk.Label(
            root,
            text="",
            justify="left",
            padx=12,
            pady=10,
            font=("Consolas", 10, "bold"),
            fg="#dc2626",
        )
        self.status.grid(row=1, column=1, sticky="n")

        self.root.bind("<KeyPress>", self.on_key)

        self.tick_job = None
        self.reset_game()

    def reset_game(self):
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.game_over = False
        self.current = self.new_piece()
        self.status.config(text="")
        self.schedule_tick()
        self.draw()

    def new_piece(self):
        name = random.choice(list(SHAPES.keys()))
        return {
            "name": name,
            "cells": SHAPES[name][:],
            "x": 3,
            "y": 0,
        }

    def rotated_cells(self, cells):
        cx, cy = 1.5, 1.5
        rotated = []
        for x, y in cells:
            rx = int(round(cx - (y - cy)))
            ry = int(round(cy + (x - cx)))
            rotated.append((rx, ry))
        return rotated

    def piece_blocks(self, piece):
        return [(piece["x"] + x, piece["y"] + y) for x, y in piece["cells"]]

    def collides(self, piece):
        for x, y in self.piece_blocks(piece):
            if x < 0 or x >= BOARD_WIDTH or y >= BOARD_HEIGHT:
                return True
            if y >= 0 and self.board[y][x] is not None:
                return True
        return False

    def try_move(self, dx=0, dy=0, rotate=False):
        if self.game_over:
            return False

        candidate = {
            "name": self.current["name"],
            "cells": self.current["cells"][:],
            "x": self.current["x"] + dx,
            "y": self.current["y"] + dy,
        }
        if rotate:
            candidate["cells"] = self.rotated_cells(candidate["cells"])

        if not self.collides(candidate):
            self.current = candidate
            self.draw()
            return True
        return False

    def lock_piece(self):
        color = COLORS[self.current["name"]]
        for x, y in self.piece_blocks(self.current):
            if y < 0:
                self.game_over = True
                self.status.config(text="Game Over\nPress R to restart")
                return
            self.board[y][x] = color

        self.clear_lines()
        self.current = self.new_piece()
        if self.collides(self.current):
            self.game_over = True
            self.status.config(text="Game Over\nPress R to restart")

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        cleared = BOARD_HEIGHT - len(new_board)
        while len(new_board) < BOARD_HEIGHT:
            new_board.insert(0, [None for _ in range(BOARD_WIDTH)])
        self.board = new_board

        if cleared > 0:
            self.lines += cleared
            line_points = {1: 100, 2: 300, 3: 500, 4: 800}
            self.score += line_points.get(cleared, cleared * 200)

    def schedule_tick(self):
        if self.tick_job is not None:
            self.root.after_cancel(self.tick_job)
        self.tick_job = self.root.after(TICK_MS, self.tick)

    def tick(self):
        if not self.game_over:
            moved = self.try_move(dy=1)
            if not moved:
                self.lock_piece()
            self.draw()
            self.schedule_tick()

    def hard_drop(self):
        while self.try_move(dy=1):
            self.score += 2
        self.lock_piece()
        self.draw()

    def on_key(self, event):
        key = event.keysym.lower()

        if key == "r":
            self.reset_game()
            return

        if self.game_over:
            return

        if key == "left":
            self.try_move(dx=-1)
        elif key == "right":
            self.try_move(dx=1)
        elif key == "down":
            if self.try_move(dy=1):
                self.score += 1
        elif key == "up":
            self.try_move(rotate=True)
        elif key == "space":
            self.hard_drop()
        self.draw()

    def draw_cell(self, x, y, color):
        x1 = x * CELL_SIZE
        y1 = y * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=color, outline="#1e293b", width=2
        )

    def draw_grid(self):
        self.canvas.delete("all")
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                color = self.board[y][x]
                if color:
                    self.draw_cell(x, y, color)
                else:
                    self.canvas.create_rectangle(
                        x * CELL_SIZE,
                        y * CELL_SIZE,
                        (x + 1) * CELL_SIZE,
                        (y + 1) * CELL_SIZE,
                        outline="#1e293b",
                        width=1,
                    )

        for x, y in self.piece_blocks(self.current):
            if y >= 0:
                self.draw_cell(x, y, COLORS[self.current["name"]])

    def draw(self):
        self.draw_grid()
        self.info.config(
            text=(
                f"Score: {self.score}\n"
                f"Lines: {self.lines}\n\n"
                "Controls:\n"
                "<- -> Move\n"
                "Up Rotate\n"
                "Down Soft drop\n"
                "Space Hard drop\n"
                "R Restart"
            )
        )


def main():
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
