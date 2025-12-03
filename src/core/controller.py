# 游戏控制器，负责协调游戏引擎和用户界面，提供统一的游戏操作接口
from core.models import GameResult, GameType, PlayerColor, Position, move_from_payload
from core import persistence
from core.ai import RandomAI, ScoringAI
from core.user_manager import UserManager
from core.replay import ReplayManager
from games.gomoku import GomokuEngine
from games.go import GoEngine
from games.reversi import ReversiEngine


def create_engine(game_type, board_size):
    # 根据游戏类型创建对应的引擎实例
    if game_type == GameType.GOMOKU:
        return GomokuEngine(board_size)
    if game_type == GameType.GO:
        return GoEngine(board_size)
    if game_type == GameType.REVERSI:
        return ReversiEngine(board_size)
    raise ValueError("Unsupported game type")


class GameController:
    def __init__(self):
        # 初始化控制器，无当前游戏
        self.engine = None
        self.game_type = None
        self.board_size = 0
        self.ai_black = None
        self.ai_white = None
        self.user_manager = UserManager()
        self.replay_manager = None
        self.is_replay_mode = False
        self.current_user_color = None

    def start_game(self, game_type, board_size):
        # 开始新游戏，创建引擎
        self.engine = create_engine(game_type, board_size)
        self.game_type = game_type
        self.board_size = board_size

    def _require_engine(self):
        # 确保有活跃游戏，否则抛异常
        if self.engine is None:
            raise ValueError("当前没有运行中的对局，请先执行开始命令。")
        return self.engine

    def place_stone(self, row, col):
        # 在指定位置落子
        engine = self._require_engine()
        position = Position(row, col)
        engine.play_move(position)

    def pass_turn(self):
        # 执行跳过回合
        engine = self._require_engine()
        engine.pass_turn()

    def undo(self):
        # 悔棋
        engine = self._require_engine()
        engine.undo()

    def resign(self, color=None):
        # 认输，默认当前玩家
        engine = self._require_engine()
        active_color = color or engine.current_player
        engine.resign(active_color)

    def restart(self):
        # 重新开始当前游戏
        engine = self._require_engine()
        engine.restart()

    def save(self, file_path):
        # 保存游戏
        engine = self._require_engine()
        payload = engine.serialize()
        payload.update(
            {
                "game_type": self.game_type.value,
                "board_size": self.board_size,
            }
        )
        persistence.save_game(file_path, payload)

    def load(self, file_path):
        # 加载游戏
        payload = persistence.load_game(file_path)
        game_type = GameType(payload["game_type"])
        board_size = payload["board_size"]
        self.start_game(game_type, board_size)
        self.engine.deserialize(payload)

    def get_board_display(self):
        # 获取棋盘文本显示
        engine = self._require_engine()
        header = "    " + " ".join(f"{i:2d}" for i in range(1, engine.board.size + 1))
        rows = [header]
        for row in range(engine.board.size):
            tokens = []
            for col in range(engine.board.size):
                cell = engine.board.get(Position(row, col))
                tokens.append(
                    "." if cell is None else "X" if cell == PlayerColor.BLACK else "O"
                )
            rows.append(f"{row + 1:2d} | " + "  ".join(tokens))
        return "\n".join(rows)

    def get_status(self):
        # 获取游戏状态信息
        engine = self._require_engine()
        snapshot = self.get_resource_snapshot()
        status_parts = [
            f"游戏: {self._game_type_label()} {self.board_size}x{self.board_size}",
            f"当前行棋方: {self._color_label(engine.current_player)}",
            self._format_resource_line(PlayerColor.BLACK, snapshot),
            self._format_resource_line(PlayerColor.WHITE, snapshot),
        ]
        if engine.is_finished():
            result = engine.get_result()
            status_parts.append(
                "结果: 平局"
                if result.winner is None
                else f"胜者: {self._color_label(result.winner)}"
            )
            status_parts.append(f"结束原因: {result.reason}")
        return " | ".join(status_parts)

    def get_resource_snapshot(self):
        # 获取资源快照（棋子数量等）
        engine = self._require_engine()
        snapshot = {}
        for color in (PlayerColor.BLACK, PlayerColor.WHITE):
            snapshot[color] = {
                "stones_on_board": engine.stones_on_board(color),
                "stones_remaining": engine.stones_remaining(color),
                "undo_remaining": engine.undo_remaining(color),
            }
        return snapshot

    def _game_type_label(self):
        # 获取游戏类型标签
        if self.game_type == GameType.GOMOKU:
            return "五子棋"
        if self.game_type == GameType.GO:
            return "围棋"
        if self.game_type == GameType.REVERSI:
            return "黑白棋"
        return "未知游戏"

    def _color_label(self, color):
        # 获取玩家颜色标签
        return "黑方" if color == PlayerColor.BLACK else "白方"

    def _format_resource_line(self, color, snapshot):
        # 格式化资源信息行
        data = snapshot[color]
        label = self._color_label(color)
        return (
            f"{label}: 在盘{data['stones_on_board']}枚，"
            f"库存{data['stones_remaining']}枚，"
            f"悔棋余量{data['undo_remaining']}次"
        )

    def set_ai(self, color, level):
        # 设置AI
        if level == 1:
            ai_class = RandomAI
        elif level == 2:
            ai_class = ScoringAI
        else:
            raise ValueError("无效AI等级")
        if color == PlayerColor.BLACK:
            self.ai_black = ai_class(color)
        else:
            self.ai_white = ai_class(color)

    def remove_ai(self, color):
        # 移除AI
        if color == PlayerColor.BLACK:
            self.ai_black = None
        else:
            self.ai_white = None

    def make_ai_move(self):
        # AI落子
        engine = self._require_engine()
        current_ai = (
            self.ai_black
            if engine.current_player == PlayerColor.BLACK
            else self.ai_white
        )
        if not current_ai:
            raise ValueError("当前玩家不是AI")
        valid_moves = self._get_valid_moves()
        if not valid_moves:
            self.pass_turn()
            return
        move_pos = current_ai.get_move(engine.board, valid_moves)
        if move_pos:
            self.place_stone(move_pos.row, move_pos.col)

    def _get_valid_moves(self):
        # 获取合法落子点
        engine = self._require_engine()
        valid_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                pos = Position(row, col)
                if engine.board.get(pos) is None:
                    if self.game_type == GameType.REVERSI:
                        flipped = engine._get_flipped_positions(
                            pos, engine.current_player
                        )
                        if flipped:
                            valid_moves.append(pos)
                    else:
                        # 对于五子棋和围棋，所有空位置都是合法的
                        valid_moves.append(pos)
        return valid_moves

    def register_user(self, username, password):
        # 用户注册
        self.user_manager.register(username, password)

    def login_user(self, username, password, color=None):
        # 用户登录
        if username == "游客":
            self.user_manager.login_guest()
        else:
            self.user_manager.login(username, password)
        self.current_user_color = color

    def logout_user(self):
        # 用户登出
        self.user_manager.logout()

    def update_user_stats(self, winner_color):
        # 代理 user_manager 更新战绩，传入当前登录用户所属颜色
        self.user_manager.update_stats(winner_color, self.current_user_color)

    def get_current_user(self):
        # 获取当前用户
        return self.user_manager.get_current_user()

    def get_user_stats(self, username=None):
        # 获取用户战绩
        return self.user_manager.get_stats(username)

    def save_replay(self, file_path):
        # 保存录像
        engine = self._require_engine()
        persistence.save_replay(
            file_path, engine.history, self.game_type, self.board_size
        )

    def load_replay(self, file_path):
        # 加载录像
        payload = persistence.load_replay(file_path)
        game_type = GameType(payload["game_type"])
        board_size = payload["board_size"]
        moves = [move_from_payload(m) for m in payload["moves"]]
        self.replay_manager = ReplayManager(moves, game_type, board_size)
        self.is_replay_mode = True

    def jump_to_replay(self, index):
        # 跳转到录像的指定步数
        if not self.replay_manager:
            raise ValueError("没有加载录像")
        self.replay_manager.jump_to(index)
        # 重置引擎并应用到当前步
        self.engine = create_engine(
            self.replay_manager.game_type, self.replay_manager.board_size
        )
        for move in self.replay_manager.moves[: self.replay_manager.current_index + 1]:
            if move.is_pass():
                self.engine.pass_turn()
            else:
                self.engine.play_move(move.position)
        self.game_type = self.replay_manager.game_type
        self.board_size = self.replay_manager.board_size

    def start_replay(self):
        # 开始回放
        if not self.replay_manager:
            raise ValueError("没有加载录像")
        self.replay_manager.start_replay()

    def stop_replay(self):
        # 停止回放
        if not self.replay_manager:
            raise ValueError("没有加载录像")
        self.replay_manager.stop_replay()
