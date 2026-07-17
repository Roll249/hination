import React from 'react';

function AlertPanel({ alerts }) {
  // If no alerts, show info message
  if (!alerts || alerts.length === 0) {
    return (
      <div className="card">
        <div className="p-4 border-b border-slate-700/50">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <span>🔔</span> Cảnh báo
          </h3>
        </div>
        <div className="p-6 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/20 flex items-center justify-center">
            <span className="text-3xl">✅</span>
          </div>
          <h4 className="text-lg font-medium text-white mb-2">Không có cảnh báo</h4>
          <p className="text-sm text-slate-400">
            Tình hình thời tiết tại khu vực này đang ổn định.
          </p>
        </div>
      </div>
    );
  }

  // Alert severity styling
  const getAlertStyles = (severity) => {
    switch (severity) {
      case 'danger':
        return {
          bg: 'bg-red-500/20',
          border: 'border-red-500/50',
          icon: '🚨',
          text: 'text-red-400',
          badge: 'bg-red-500/30 text-red-300'
        };
      case 'warning':
        return {
          bg: 'bg-orange-500/20',
          border: 'border-orange-500/50',
          icon: '⚠️',
          text: 'text-orange-400',
          badge: 'bg-orange-500/30 text-orange-300'
        };
      default:
        return {
          bg: 'bg-blue-500/20',
          border: 'border-blue-500/50',
          icon: 'ℹ️',
          text: 'text-blue-400',
          badge: 'bg-blue-500/30 text-blue-300'
        };
    }
  };

  // Alert type styling
  const getAlertTypeLabel = (type) => {
    switch (type) {
      case 'heavy_rain':
        return 'Mưa lớn';
      case 'extreme_rain':
        return 'Mưa cực đoan';
      case 'cold_wave':
        return 'Sóng lạnh';
      case 'frost':
        return 'Sương giá';
      case 'storm':
        return 'Bão';
      case 'high_humidity':
        return 'Độ ẩm cao';
      default:
        return 'Thông báo';
    }
  };

  return (
    <div className="card">
      <div className="p-4 border-b border-slate-700/50 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span>🔔</span> Cảnh báo
        </h3>
        <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs font-medium rounded-full">
          {alerts.length} cảnh báo
        </span>
      </div>
      
      <div className="p-4 space-y-3">
        {alerts.map((alert, index) => {
          const styles = getAlertStyles(alert.severity);
          return (
            <div 
              key={index}
              className={`p-4 rounded-lg ${styles.bg} border ${styles.border} ${styles.text} animate-slide-up`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{styles.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${styles.badge}`}>
                      {getAlertTypeLabel(alert.type)}
                    </span>
                    <span className="text-xs opacity-70">
                      {alert.timestamp ? new Date(alert.timestamp).toLocaleString('vi-VN') : 'Vừa xong'}
                    </span>
                  </div>
                  <p className="font-medium">{alert.message || alert.action}</p>
                  {alert.value && (
                    <p className="text-sm opacity-70 mt-1">
                      Giá trị: {alert.value} {alert.unit}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recommended Actions */}
      <div className="p-4 border-t border-slate-700/50 bg-slate-800/30">
        <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
          <span>📋</span> Hành động khuyến nghị
        </h4>
        <ul className="space-y-1 text-sm text-slate-400">
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            Theo dõi tin tức địa phương
          </li>
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            Chuẩn bị vật tư khẩn cấp
          </li>
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            Thông báo cho người thân
          </li>
        </ul>
      </div>
    </div>
  );
}

export default AlertPanel;
