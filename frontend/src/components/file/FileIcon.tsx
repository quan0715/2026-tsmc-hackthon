import { File } from 'lucide-react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faPython,
  faJs,
  faGolang,
  faRust,
  faJava,
  faPhp,
  faHtml5,
  faCss3Alt,
  faSass,
  faReact,
  faVuejs,
  faAngular,
  faDocker,
  faGitAlt,
  faMarkdown,
  faNodeJs,
} from '@fortawesome/free-brands-svg-icons'
import { faFileCode, faFileAlt, faDatabase, faCog } from '@fortawesome/free-solid-svg-icons'
import { memo } from 'react'

interface FileIconProps {
  filename: string
  className?: string
}

export const FileIcon = memo(function FileIcon({ filename, className = 'w-4 h-4 flex-shrink-0' }: FileIconProps) {
  const ext = filename.split('.').pop()?.toLowerCase()
  const lowerName = filename.toLowerCase()

  // 特殊檔案名稱
  if (lowerName === 'dockerfile' || lowerName.startsWith('dockerfile.')) {
    return <FontAwesomeIcon icon={faDocker} className={`${className} text-blue-400`} />
  }
  if (lowerName === '.gitignore' || lowerName === '.gitattributes') {
    return <FontAwesomeIcon icon={faGitAlt} className={`${className} text-orange-500`} />
  }

  // 根據副檔名選擇 icon
  switch (ext) {
    // Python
    case 'py':
    case 'pyw':
    case 'pyi':
      return <FontAwesomeIcon icon={faPython} className={`${className} text-yellow-400`} />
    
    // JavaScript / TypeScript
    case 'js':
    case 'mjs':
    case 'cjs':
      return <FontAwesomeIcon icon={faJs} className={`${className} text-yellow-400`} />
    case 'ts':
      return <FontAwesomeIcon icon={faJs} className={`${className} text-blue-400`} />
    case 'jsx':
    case 'tsx':
      return <FontAwesomeIcon icon={faReact} className={`${className} text-cyan-400`} />
    
    // Go
    case 'go':
      return <FontAwesomeIcon icon={faGolang} className={`${className} text-cyan-400`} />
    
    // Rust
    case 'rs':
      return <FontAwesomeIcon icon={faRust} className={`${className} text-orange-400`} />
    
    // Java
    case 'java':
      return <FontAwesomeIcon icon={faJava} className={`${className} text-red-400`} />
    
    // PHP
    case 'php':
      return <FontAwesomeIcon icon={faPhp} className={`${className} text-purple-400`} />
    
    // Web
    case 'html':
    case 'htm':
      return <FontAwesomeIcon icon={faHtml5} className={`${className} text-orange-500`} />
    case 'css':
      return <FontAwesomeIcon icon={faCss3Alt} className={`${className} text-blue-500`} />
    case 'scss':
    case 'sass':
      return <FontAwesomeIcon icon={faSass} className={`${className} text-pink-400`} />
    
    // Frameworks
    case 'vue':
      return <FontAwesomeIcon icon={faVuejs} className={`${className} text-green-400`} />
    case 'ng':
      return <FontAwesomeIcon icon={faAngular} className={`${className} text-red-500`} />
    
    // Markdown
    case 'md':
    case 'mdx':
      return <FontAwesomeIcon icon={faMarkdown} className={`${className} text-blue-300`} />
    
    // Config / Data
    case 'json':
      return <FontAwesomeIcon icon={faFileCode} className={`${className} text-yellow-300`} />
    case 'yml':
    case 'yaml':
      return <FontAwesomeIcon icon={faCog} className={`${className} text-purple-300`} />
    case 'sql':
      return <FontAwesomeIcon icon={faDatabase} className={`${className} text-blue-400`} />
    case 'env':
      return <FontAwesomeIcon icon={faCog} className={`${className} text-yellow-500`} />
    
    // Node
    case 'node':
      return <FontAwesomeIcon icon={faNodeJs} className={`${className} text-green-500`} />
    
    // 其他程式碼檔案
    case 'c':
    case 'cpp':
    case 'h':
    case 'hpp':
    case 'cs':
    case 'rb':
    case 'sh':
    case 'bash':
    case 'zsh':
      return <FontAwesomeIcon icon={faFileCode} className={`${className} text-gray-400`} />
    
    // 文字檔案
    case 'txt':
    case 'log':
      return <FontAwesomeIcon icon={faFileAlt} className={`${className} text-gray-400`} />
    
    // 預設
    default:
      return <File className={`${className} text-gray-400`} />
  }
})
