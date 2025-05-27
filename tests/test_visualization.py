"""Unit tests for the visualization system."""

from game.board import Board
from game.visualization import Visualization

def test_visualization_initialization():
    """Test basic visualization setup."""
    board = Board(10, 10)
    vis = Visualization(board)
    assert vis.enabled == True
    assert vis.board == board
    assert vis.frame_count == 0

def test_visualization_toggle():
    """Test enabling/disabling visualization."""
    board = Board(10, 10)
    vis = Visualization(board)
    assert vis.enabled == True
    vis.toggle()
    assert vis.enabled == False
    vis.toggle()
    assert vis.enabled == True

def test_collect_empty_stats():
    """Test statistics collection on empty board."""
    board = Board(5, 5)
    vis = Visualization(board)
    stats = vis._collect_stats()
    
    assert stats["turn"] == 0
    assert stats["units"]["total"] == 0
    assert stats["plants"]["total"] == 0

def test_generate_snapshot():
    """Test snapshot generation."""
    board = Board(3, 3)
    vis = Visualization(board)
    snapshot = vis.generate_snapshot()
    
    # Basic snapshot content checks
    assert "Game State Snapshot" in snapshot
    assert "Turn: 0" in snapshot
    assert "Board State:" in snapshot
    assert "Legend:" in snapshot
