"""Security sanitization function tests"""
import pytest
from app.services.container_service import (
    _sanitize_git_url,
    _sanitize_branch_name,
    _sanitize_path
)


class TestSanitizeGitUrl:
    """Git URL sanitization tests"""

    def test_valid_https_url(self):
        """Test valid HTTPS URLs pass validation"""
        valid_urls = [
            "https://github.com/user/repo.git",
            "https://github.com/user/repo",
            "https://gitlab.com/user/repo.git",
            "http://internal-git.company.com/project/repo.git",
        ]
        for url in valid_urls:
            result = _sanitize_git_url(url)
            assert result == url

    def test_valid_ssh_url(self):
        """Test valid SSH URLs pass validation"""
        valid_urls = [
            "git@github.com:user/repo.git",
            "git@gitlab.com:org/project.git",
        ]
        for url in valid_urls:
            result = _sanitize_git_url(url)
            assert result == url

    def test_empty_url_rejected(self):
        """Test empty URL is rejected"""
        with pytest.raises(ValueError, match="不能為空"):
            _sanitize_git_url("")

    def test_none_url_rejected(self):
        """Test None URL is rejected"""
        with pytest.raises(ValueError, match="不能為空"):
            _sanitize_git_url(None)

    def test_shell_injection_semicolon_rejected(self):
        """Test URL with semicolon (command chaining) is rejected"""
        with pytest.raises(ValueError):
            _sanitize_git_url("https://github.com/user/repo.git; rm -rf /")

    def test_shell_injection_ampersand_rejected(self):
        """Test URL with ampersand (background execution) is rejected"""
        with pytest.raises(ValueError):
            _sanitize_git_url("https://github.com/user/repo.git & malicious")

    def test_shell_injection_pipe_rejected(self):
        """Test URL with pipe (piping) is rejected"""
        with pytest.raises(ValueError):
            _sanitize_git_url("https://github.com/user/repo.git | cat /etc/passwd")

    def test_shell_injection_backtick_rejected(self):
        """Test URL with backtick (command substitution) is rejected"""
        with pytest.raises(ValueError):
            _sanitize_git_url("https://github.com/user/`whoami`.git")

    def test_shell_injection_dollar_rejected(self):
        """Test URL with dollar sign (variable expansion) is rejected"""
        with pytest.raises(ValueError):
            _sanitize_git_url("https://github.com/user/$USER.git")

    def test_newline_injection_rejected(self):
        """Test URL with newline is rejected"""
        with pytest.raises(ValueError):
            _sanitize_git_url("https://github.com/user/repo.git\nrm -rf /")


class TestSanitizeBranchName:
    """Branch name sanitization tests"""

    def test_valid_branch_names(self):
        """Test valid branch names pass validation"""
        valid_branches = [
            "main",
            "master",
            "develop",
            "feature/new-feature",
            "release-1.0",
            "hotfix_urgent",
            "v1.0.0",
        ]
        for branch in valid_branches:
            result = _sanitize_branch_name(branch)
            assert result == branch

    def test_empty_branch_defaults_to_main(self):
        """Test empty branch defaults to 'main'"""
        assert _sanitize_branch_name("") == "main"
        assert _sanitize_branch_name(None) == "main"

    def test_shell_injection_semicolon_rejected(self):
        """Test branch with semicolon is rejected"""
        with pytest.raises(ValueError, match="無效的 branch"):
            _sanitize_branch_name("main; rm -rf /")

    def test_shell_injection_ampersand_rejected(self):
        """Test branch with ampersand is rejected"""
        with pytest.raises(ValueError, match="無效的 branch"):
            _sanitize_branch_name("main & echo hacked")

    def test_double_dot_rejected(self):
        """Test branch with .. is rejected"""
        with pytest.raises(ValueError, match="無效的 branch"):
            _sanitize_branch_name("feature/../../../etc/passwd")

    def test_double_slash_rejected(self):
        """Test branch with // is rejected"""
        with pytest.raises(ValueError, match="無效的 branch"):
            _sanitize_branch_name("feature//something")

    def test_leading_dot_rejected(self):
        """Test branch starting with . is rejected"""
        with pytest.raises(ValueError, match="無效的 branch"):
            _sanitize_branch_name(".hidden")

    def test_trailing_dot_rejected(self):
        """Test branch ending with . is rejected"""
        with pytest.raises(ValueError, match="無效的 branch"):
            _sanitize_branch_name("branch.")


class TestSanitizePath:
    """Path sanitization tests"""

    def test_valid_relative_paths(self):
        """Test valid relative paths pass validation"""
        result = _sanitize_path("repo/src/main.py", "/workspace")
        assert result == "/workspace/repo/src/main.py"

    def test_valid_absolute_paths(self):
        """Test valid absolute paths within base_path pass validation"""
        result = _sanitize_path("/workspace/repo/file.txt", "/workspace")
        assert result == "/workspace/repo/file.txt"

    def test_empty_path_rejected(self):
        """Test empty path is rejected"""
        with pytest.raises(ValueError, match="不能為空"):
            _sanitize_path("", "/workspace")

    def test_path_traversal_rejected(self):
        """Test path with .. is rejected"""
        with pytest.raises(ValueError, match="不能包含"):
            _sanitize_path("../../../etc/passwd", "/workspace")

    def test_path_traversal_in_middle_rejected(self):
        """Test path with .. in middle is rejected"""
        with pytest.raises(ValueError, match="不能包含"):
            _sanitize_path("repo/../../../etc/passwd", "/workspace")

    def test_url_encoded_path_traversal_rejected(self):
        """Test URL-encoded path traversal is rejected"""
        with pytest.raises(ValueError, match="不能包含"):
            _sanitize_path("repo/%2e%2e/secret", "/workspace")

    def test_double_url_encoded_path_traversal_rejected(self):
        """Test double URL-encoded path traversal is rejected"""
        with pytest.raises(ValueError, match="不能包含"):
            _sanitize_path("repo/%252e%252e/secret", "/workspace")

    def test_shell_injection_semicolon_rejected(self):
        """Test path with semicolon is rejected"""
        with pytest.raises(ValueError, match="不允許的字元"):
            _sanitize_path("file.txt; rm -rf /", "/workspace")

    def test_shell_injection_backtick_rejected(self):
        """Test path with backtick is rejected"""
        with pytest.raises(ValueError, match="不允許的字元"):
            _sanitize_path("`whoami`.txt", "/workspace")

    def test_single_quote_rejected(self):
        """Test path with single quote is rejected"""
        with pytest.raises(ValueError, match="不允許的字元"):
            _sanitize_path("file'name.txt", "/workspace")

    def test_double_quote_rejected(self):
        """Test path with double quote is rejected"""
        with pytest.raises(ValueError, match="不允許的字元"):
            _sanitize_path('file"name.txt', "/workspace")

    def test_path_outside_base_rejected(self):
        """Test path outside base_path is rejected"""
        with pytest.raises(ValueError, match="必須在"):
            _sanitize_path("/etc/passwd", "/workspace")

    def test_newline_injection_rejected(self):
        """Test path with newline is rejected"""
        with pytest.raises(ValueError, match="不允許的字元"):
            _sanitize_path("file.txt\nrm -rf /", "/workspace")
