import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card'
import { apiErrorMessage } from '@/utils/apiError'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // 前端驗證
    if (username.length < 3) {
      setError('使用者名稱必須至少 3 個字元')
      return
    }

    if (password.length < 8) {
      setError('密碼必須至少 8 個字元')
      return
    }

    try {
      setLoading(true)
      setError('')
      await login(username, password)
      navigate('/projects')
    } catch (err: any) {
      // 詳細的錯誤處理
      const status = err.response?.status

      if (status === 401) {
        setError('❌ 使用者名稱或密碼錯誤，請重新輸入')
      } else if (status === 422) {
        setError('⚠️ 輸入格式不正確，請檢查使用者名稱和密碼')
      } else if (status === 500) {
        setError('🔧 伺服器錯誤，請稍後再試')
      } else if (err.code === 'ERR_NETWORK') {
        setError('📡 無法連線到伺服器，請檢查網路連線')
      } else {
        setError(apiErrorMessage(err, '登入失敗，請重試'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex justify-center mb-4">
            <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center text-white text-xl font-bold">
              smo
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center text-gray-100">
            AI 舊程式碼智能重構系統
          </CardTitle>
          <p className="text-center text-sm text-gray-400">登入以繼續</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-200">使用者名稱</label>
              <Input
                type="text"
                placeholder="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-200">密碼</label>
              <Input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <div className="bg-red-900/30 border border-red-700/50 text-red-400 p-4 rounded-lg flex items-start gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <span className="text-xl flex-shrink-0">⚠️</span>
                <div className="flex-1">
                  <div className="font-semibold mb-1">登入失敗</div>
                  <div className="text-sm">{error}</div>
                </div>
              </div>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? '登入中...' : '登入'}
            </Button>

            <div className="text-center text-sm text-gray-400">
              沒有帳號？{' '}
              <Link to="/register" className="text-purple-400 hover:underline">
                註冊
              </Link>
            </div>

            <div className="text-center text-sm text-gray-500 mt-4">
              測試帳號: quan / quan12345
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
