# AI模块，实现不同级别的AI算法
import random
from core.models import PlayerColor, Position


class RandomAI:
    def __init__(self, color):
        self.color = color

    def get_move(self, board, valid_moves):
        # 随机选择合法落子点
        if not valid_moves:
            return None
        return random.choice(valid_moves)


class ScoringAI:
    def __init__(self, color):
        self.color = color

    def get_move(self, board, valid_moves):
        # 基于评分函数选择最佳落子点
        if not valid_moves:
            return None
        best_move = None
        best_score = -float("inf")
        for move in valid_moves:
            score = self._evaluate_move(board, move)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def _evaluate_move(self, board, position):
        # 简单评分：位置权重 + 翻转数量
        score = 0
        if board.size == 8:
            weights = [
                [100, -20, 10, 5, 5, 10, -20, 100],
                [-20, -40, -2, -2, -2, -2, -40, -20],
                [10, -2, 5, 1, 1, 5, -2, 10],
                [5, -2, 1, 1, 1, 1, -2, 5],
                [5, -2, 1, 1, 1, 1, -2, 5],
                [10, -2, 5, 1, 1, 5, -2, 10],
                [-20, -40, -2, -2, -2, -2, -40, -20],
                [100, -20, 10, 5, 5, 10, -20, 100],
            ]
            score = weights[position.row][position.col]
        # 模拟翻转计算（简化版）
        flipped_count = len(self._get_flipped_positions(board, position, self.color))
        score += flipped_count * 10
        return score

    def _get_flipped_positions(self, board, position, color):
        # 简化版翻转计算（与reversi.py类似）
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
            line_flipped = self._get_line_flipped(board, position, color, dr, dc)
            flipped.extend(line_flipped)
        return flipped

    def _get_line_flipped(self, board, position, color, dr, dc):
        opponent = color.opponent()
        r, c = position.row + dr, position.col + dc
        to_flip = []
        while 0 <= r < board.size and 0 <= c < board.size:
            cell = board.get(Position(r, c))
            if cell == opponent:
                to_flip.append(Position(r, c))
            elif cell == color:
                return to_flip
            else:
                break
            r += dr
            c += dc
        return []
