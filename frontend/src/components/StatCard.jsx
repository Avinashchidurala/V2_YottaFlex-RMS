import clsx from 'clsx'

export default function StatCard({ label, value, icon: Icon, trend, trendLabel, color = 'blue', subtitle }) {
  const colorMap = {
    blue: { bg: 'bg-blue-50', text: 'text-blue-600', iconBg: 'bg-blue-100' },
    green: { bg: 'bg-green-50', text: 'text-green-600', iconBg: 'bg-green-100' },
    red: { bg: 'bg-red-50', text: 'text-red-600', iconBg: 'bg-red-100' },
    orange: { bg: 'bg-orange-50', text: 'text-orange-600', iconBg: 'bg-orange-100' },
    purple: { bg: 'bg-purple-50', text: 'text-purple-600', iconBg: 'bg-purple-100' },
    yellow: { bg: 'bg-yellow-50', text: 'text-yellow-600', iconBg: 'bg-yellow-100' },
  }
  const c = colorMap[color] || colorMap.blue

  const trendPositive = trend > 0
  const trendNeutral = trend === 0 || trend === undefined

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-500 font-medium truncate">{label}</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 truncate">{value ?? '—'}</p>
          {subtitle && <p className="mt-0.5 text-xs text-gray-400 truncate">{subtitle}</p>}
          {trend !== undefined && (
            <div className="mt-2 flex items-center gap-1">
              <span
                className={clsx(
                  'text-xs font-medium',
                  trendNeutral ? 'text-gray-400' : trendPositive ? 'text-green-600' : 'text-red-500'
                )}
              >
                {trendNeutral ? '—' : trendPositive ? `▲ ${trend}%` : `▼ ${Math.abs(trend)}%`}
              </span>
              {trendLabel && <span className="text-xs text-gray-400">{trendLabel}</span>}
            </div>
          )}
        </div>
        {Icon && (
          <div className={clsx('w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ml-3', c.iconBg)}>
            <Icon className={clsx('w-6 h-6', c.text)} />
          </div>
        )}
      </div>
    </div>
  )
}
