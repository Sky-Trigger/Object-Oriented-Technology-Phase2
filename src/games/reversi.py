# 黑白棋游戏引擎，实现黑白棋规则，包括落子、翻转和胜负判断
from core.game_engine import GameEngine
from core.models import GameResult, Move, PlayerColor, Position


class ReversiEngine(GameEngine):
    def __init__(self, board_size=8, max_undo=3):
        # 初始化黑白棋引擎，棋盘大小固定为8x8
        if board_size != 8:
            raise ValueError("黑白棋棋盘大小必须为8x8")
        super().__init__(board_size, max_undo)
        self._initialize_board()

    def _initialize_board(self):
        # 初始化黑白棋初始布局
        center = self.board.size // 2
        self.board.set(Position(center - 1, center - 1), PlayerColor.WHITE)
        self.board.set(Position(center - 1, center), PlayerColor.BLACK)
        self.board.set(Position(center, center - 1), PlayerColor.BLACK)
        self.board.set(Position(center, center), PlayerColor.WHITE)
        self._recalculate_stone_counters()

    def play_move(self, position):
        # 执行落子，检查合法性并翻转棋子
        if self.is_finished():
            raise ValueError("当前对局已结束")
        if not self.board.is_within_bounds(position):
            raise ValueError("落子超出棋盘范围")
        if self.board.get(position) is not None:
            raise ValueError("该位置已有棋子")
        current_color = self.current_player
        flipped = self._get_flipped_positions(position, current_color)
        if not flipped:
            raise ValueError("该位置不是合法落子点")
        self.board.set(position, current_color)
        for pos in flipped:
            self.board.set(pos, current_color)
        self._record_stone_placed(current_color)
        self._record_stone_placed(current_color)  # 落子本身
        for _ in flipped:
            self._record_stone_removed(current_color.opponent())
            self._record_stone_placed(current_color)
        move = Move(position, current_color, flipped)
        self._push_move(move)
        self._check_game_end()

    def _get_flipped_positions(self, position, color):
        # 获取落子后可翻转的位置
        directions = [
            (0, 1),
            (1, 0),
            (0, -1),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]
        flipped = []
        for dr, dc in directions:
            line_flipped = self._get_line_flipped(position, color, dr, dc)
            flipped.extend(line_flipped)
        return flipped

    def _get_line_flipped(self, position, color, dr, dc):
        # 获取单方向上的翻转位置
        opponent = color.opponent()
        r, c = position.row + dr, position.col + dc
        to_flip = []
        while 0 <= r < self.board.size and 0 <= c < self.board.size:
            cell = self.board.get(Position(r, c))
            if cell == opponent:
                to_flip.append(Position(r, c))
            elif cell == color:
                return to_flip
            else:
                break
            r += dr
            c += dc
        return []

    def _check_game_end(self):
        # 检查游戏是否结束
        if self._is_board_full():
            self._winner = self._score_game()
        elif not self._has_valid_moves(
            self.current_player
        ) and not self._has_valid_moves(self.current_player.opponent()):
            self._winner = self._score_game()

    def _is_board_full(self):
        # 检查棋盘是否已满
        for row in range(self.board.size):
            for col in range(self.board.size):
                if self.board.get(Position(row, col)) is None:
                    return False
        return True

    def _has_valid_moves(self, color):
        # 检查玩家是否有合法落子点
        for row in range(self.board.size):
            for col in range(self.board.size):
                pos = Position(row, col)
                if self.board.get(pos) is None and self._get_flipped_positions(
                    pos, color
                ):
                    return True
        return False

    def _score_game(self):
        # 计算游戏得分
        black_count = self.stones_on_board(PlayerColor.BLACK)
        white_count = self.stones_on_board(PlayerColor.WHITE)
        if black_count > white_count:
            return GameResult(
                PlayerColor.BLACK, f"黑方以 {black_count}:{white_count} 获胜"
            )
        elif white_count > black_count:
            return GameResult(
                PlayerColor.WHITE, f"白方以 {white_count}:{black_count} 获胜"
            )
        else:
            return GameResult(None, "双方棋子数相同，平局")

    def pass_turn(self):
        # 执行虚手，如果无合法落子则跳过
        if self.is_finished():
            raise ValueError("当前对局已结束")
        if self._has_valid_moves(self.current_player):
            raise ValueError("当前玩家有合法落子点，不能虚手")
        move = Move(None, self.current_player)
        self._push_move(move)
        self._check_game_end()

    def _undo_internal(self):
        # 悔棋内部逻辑
        last_move = self.history.pop()
        self.current_player = last_move.color
        if last_move.position is not None:
            self.board.set(last_move.position, None)
            self._record_stone_removed(last_move.color)
            for pos in last_move.captures:
                self.board.set(pos, last_move.color.opponent())
                self._record_stone_removed(last_move.color)
                self._record_stone_placed(last_move.color.opponent())
        self._winner = None
