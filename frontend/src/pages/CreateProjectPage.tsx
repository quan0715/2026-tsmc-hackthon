import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { createProjectAPI } from '@/services/project.service'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'

export default function CreateProjectPage() {
  const navigate = useNavigate()
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [initPrompt, setInitPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError('')
      const project = await createProjectAPI({
        repo_url: repoUrl,
        branch,
        init_prompt: initPrompt,
      })
      navigate(`/projects/${project.id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || '建立專案失敗')
      console.error('建立專案失敗', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
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
              <div>
                <label className="block text-sm font-medium mb-2">
                  Repository URL *
                </label>
                <Input
                  placeholder="https://github.com/username/repo.git"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  支援 HTTPS 和 SSH 格式的 Git repository URL
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  分支 *
                </label>
                <Input
                  placeholder="main"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  預設為 main 分支
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  初始提示 *
                </label>
                <Textarea
                  placeholder="描述你想要 AI 執行的重構任務..."
                  value={initPrompt}
                  onChange={(e) => setInitPrompt(e.target.value)}
                  rows={6}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  例如：「重構所有的 API 路由，使用 async/await 語法」
                </p>
              </div>

              {error && (
                <div className="text-sm text-red-500 bg-red-50 p-3 rounded">
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
