interface Props {
  label: string
  variant?: 'company' | 'degree' | 'tool' | 'location' | 'misc'
}

const icons: Record<string, string> = {
  company: '🏢',
  degree: '🎓',
  tool: '🔧',
  location: '📍',
  misc: '🏷️',
}

export default function SkillTag({ label, variant = 'misc' }: Props) {
  return (
    <span className={`tag tag-${variant}`}>
      <span>{icons[variant]}</span>
      {label}
    </span>
  )
}
