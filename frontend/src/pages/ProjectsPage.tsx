import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { getProjectsAPI } from '@/services/project.service'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Project } from '@/types/project.types'

const statusColors: Record<string, 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
  CREATED: 'secondary',
  PROVISIONING: 'warning',
  READY: 'success',
  RUNNING: 'default',
  STOPPED: 'secondary',
  FAILED: 'destructive',
}

export default function ProjectsPage() {
  const { user, logout } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const data = await getProjectsAPI()
      setProjects(data.projects)
    } catch (error) {
      console.error('載入專案失敗', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-lg text-gray-300">載入中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-orange-500 rounded flex items-center justify-center text-white text-sm font-bold">
              smo
            </div>
            <h1 className="text-xl font-bold">AI 舊程式碼智能重構系統</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">
              {user?.username} ({user?.email})
            </span>
            <Button variant="outline" size="sm" onClick={logout}>
              登出
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto p-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold">我的專案</h2>
          <Link to="/projects/new">
            <Button>+ 建立專案</Button>
          </Link>
        </div>

        {projects.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <p className="text-gray-400 mb-4">尚無專案</p>
              <Link to="/projects/new">
                <Button>建立第一個專案</Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`}>
                <Card className="hover:border-purple-500/50 transition-all cursor-pointer h-full">
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate text-gray-100" title={project.title || project.repo_url}>
                          {project.title || project.repo_url?.split('/').pop()?.replace('.git', '') || '未命名專案'}
                        </h3>
                        {project.repo_url && (
                          <p className="text-xs text-gray-500 truncate">{project.repo_url}</p>
                        )}
                      </div>
                      <Badge variant={statusColors[project.status]}>
                        {project.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-400 line-clamp-2 mb-2">
                      {project.description || project.init_prompt}
                    </p>
                    <div className="text-xs text-gray-500">
                      <div>分支: {project.branch}</div>
                      <div>建立於: {new Date(project.created_at).toLocaleString('zh-TW')}</div>
                    </div>
                    {project.last_error && (
                      <div className="mt-2 text-xs text-red-400 bg-red-900/30 p-2 rounded border border-red-700/50">
                        錯誤: {project.last_error}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
