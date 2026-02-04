import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { createProjectAPI } from '@/services/project.service'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import { ProjectType } from '@/types/project.types'
import { GitBranch, MessageSquare } from 'lucide-react'

export default function CreateProjectPage() {
  const navigate = useNavigate()
  const [projectType, setProjectType] = useState<ProjectType>(ProjectType.REFACTOR)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [spec, setSpec] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [urlWarning, setUrlWarning] = useState('')
  const [suggestedUrl, setSuggestedUrl] = useState('')

  /**
   * 驗證並修正 Git repository URL
   */
  const validateAndFixUrl = (url: string) => {
    setUrlWarning('')
    setSuggestedUrl('')

    if (!url) return

    // 檢測常見錯誤：GitHub 網頁 URL
    if (url.includes('/tree/') || url.includes('/blob/') || url.includes('?tab=')) {
      const match = url.match(/https?:\/\/github\.com\/([^\/]+)\/([^\/\?]+)/)
      if (match) {
        const [, owner, repo] = match
        const correctedUrl = `https://github.com/${owner}/${repo}.git`
        setUrlWarning('⚠️ 您輸入的是 GitHub 網頁 URL，而不是 Git repository URL')
        setSuggestedUrl(correctedUrl)
      }
    }
    // 檢測 GitHub URL 但缺少 .git
    else if (url.match(/^https?:\/\/github\.com\/[^\/]+\/[^\/]+$/) && !url.endsWith('.git')) {
      setUrlWarning('💡 建議在 GitHub URL 後加上 .git 後綴')
      setSuggestedUrl(`${url}.git`)
    }
  }

  const handleUrlChange = (value: string) => {
    setRepoUrl(value)
    validateAndFixUrl(value)
  }

  const handleUseSuggestedUrl = () => {
    if (suggestedUrl) {
      setRepoUrl(suggestedUrl)
      setUrlWarning('')
      setSuggestedUrl('')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError('')
      const project = await createProjectAPI({
        title: title || undefined,
        description: description || undefined,
        project_type: projectType,
        repo_url: projectType === ProjectType.REFACTOR ? repoUrl : undefined,
        branch,
        spec,
      })
      // Sandbox 專案導向聊天頁面，重構專案導向詳情頁面
      if (projectType === ProjectType.SANDBOX) {
        navigate(`/projects/${project.id}/chat`)
      } else {
        navigate(`/projects/${project.id}`)
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || '建立專案失敗')
      console.error('建立專案失敗', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800">
        <div className="container mx-auto px-4 py-4">
          <Link to="/projects">
            <Button variant="ghost" size="sm">
              ← 返回專案列表
            </Button>
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto p-8 max-w-2xl">
        <h1 className="text-3xl font-bold mb-8">建立新專案</h1>

        <Card>
          <CardHeader>
            <CardTitle>專案資訊</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* 專案類型選擇 */}
              <div>
                <label className="block text-sm font-medium mb-3 text-gray-200">
                  專案類型
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    type="button"
                    onClick={() => setProjectType(ProjectType.REFACTOR)}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      projectType === ProjectType.REFACTOR
                        ? 'border-blue-500 bg-blue-900/30'
                        : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                    }`}
                  >
                    <GitBranch className={`w-6 h-6 mb-2 ${
                      projectType === ProjectType.REFACTOR ? 'text-blue-400' : 'text-gray-400'
                    }`} />
                    <div className="font-medium text-gray-200">重構專案</div>
                    <div className="text-xs text-gray-400 mt-1">
                      Clone 一個 Git repository 進行程式碼重構
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setProjectType(ProjectType.SANDBOX)}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      projectType === ProjectType.SANDBOX
                        ? 'border-purple-500 bg-purple-900/30'
                        : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                    }`}
                  >
                    <MessageSquare className={`w-6 h-6 mb-2 ${
                      projectType === ProjectType.SANDBOX ? 'text-purple-400' : 'text-gray-400'
                    }`} />
                    <div className="font-medium text-gray-200">沙盒測試</div>
                    <div className="text-xs text-gray-400 mt-1">
                      建立空的工作空間，與 AI Agent 自由對話
                    </div>
                  </button>
                </div>
              </div>

              {/* 專案標題 */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-200">
                  專案標題
                </label>
                <Input
                  placeholder="選填，未填則使用 repository 名稱"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              {/* 專案描述 */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-200">
                  專案描述
                </label>
                <Textarea
                  placeholder="選填，描述專案目標"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                />
              </div>

              {/* Repository URL - 只在 REFACTOR 類型顯示 */}
              {projectType === ProjectType.REFACTOR && (
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-200">
                    Repository URL *
                  </label>
                  <Input
                    placeholder="https://github.com/username/repo.git"
                    value={repoUrl}
                    onChange={(e) => handleUrlChange(e.target.value)}
                    required
                    className={urlWarning ? 'border-yellow-500' : ''}
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    支援 HTTPS 和 SSH 格式的 Git repository URL
                  </p>

                  {/* URL 警告和建議 */}
                  {urlWarning && (
                    <div className="mt-2 p-3 bg-yellow-900/30 border border-yellow-700/50 rounded text-sm">
                      <p className="text-yellow-400 mb-2">{urlWarning}</p>
                      {suggestedUrl && (
                        <div className="space-y-2">
                          <p className="font-mono text-xs text-yellow-300 bg-yellow-900/50 p-2 rounded">
                            建議使用：{suggestedUrl}
                          </p>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={handleUseSuggestedUrl}
                            className="text-yellow-400 border-yellow-600 hover:bg-yellow-900/30"
                          >
                            使用建議的 URL
                          </Button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 範例說明 */}
                  <div className="mt-2 text-xs text-gray-400">
                    <p className="font-medium mb-1">正確格式範例：</p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li className="font-mono">https://github.com/username/repo.git</li>
                      <li className="font-mono">git@github.com:username/repo.git</li>
                    </ul>
                  </div>
                </div>
              )}

              {/* Branch - 只在 REFACTOR 類型顯示 */}
              {projectType === ProjectType.REFACTOR && (
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-200">
                    分支 *
                  </label>
                  <Input
                    placeholder="main"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    required
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    預設為 main 分支
                  </p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-200">
                  {projectType === ProjectType.SANDBOX ? '初始訊息 *' : 'Spec *'}
                </label>
                <Textarea
                  placeholder={
                    projectType === ProjectType.SANDBOX
                      ? '描述你想要 AI Agent 做什麼...\n例如：「建立一個簡單的 TODO 應用」'
                      : '描述你想要 AI 執行的重構任務和規格...'
                  }
                  value={spec}
                  onChange={(e) => setSpec(e.target.value)}
                  rows={6}
                  required
                />
                <p className="text-xs text-gray-400 mt-1">
                  {projectType === ProjectType.SANDBOX
                    ? '這將作為與 AI Agent 的第一則對話訊息'
                    : '描述重構目標、期望結果和任何特定規格要求'}
                </p>
              </div>

              {error && (
                <div className="text-sm text-red-400 bg-red-900/30 p-3 rounded border border-red-700/50">
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <Button type="submit" className="flex-1" disabled={loading}>
                  {loading ? '建立中...' : '建立專案'}
                </Button>
                <Link to="/projects" className="flex-1">
                  <Button type="button" variant="outline" className="w-full">
                    取消
                  </Button>
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
