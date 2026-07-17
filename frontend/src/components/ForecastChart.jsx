import React, { useRef, useEffect } from 'react';
import Chart from 'chart.js/auto';

function ForecastChart({ districtData }) {
  const chartRef = useRef(null);
  const chartInstanceRef = useRef(null);

  // Generate 7-day forecast data
  const generateForecastData = () => {
    const days = [];
    const tempsHigh = [];
    const tempsLow = [];
    const rainfall = [];
    
    const baseTemp = districtData?.current?.temp || 25;
    const baseRain = districtData?.current?.rainfall || 0;
    
    for (let i = 0; i < 7; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);
      
      // Add some variation
      const variation = Math.sin(i * 0.5) * 3;
      const rainVariation = Math.random() * 20;
      
      days.push(date.toLocaleDateString('vi-VN', { weekday: 'short', day: 'numeric' }));
      tempsHigh.push(Math.round(baseTemp + variation + 2));
      tempsLow.push(Math.round(baseTemp + variation - 3));
      rainfall.push(Math.round(baseRain + rainVariation));
    }
    
    return { days, tempsHigh, tempsLow, rainfall };
  };

  useEffect(() => {
    if (!chartRef.current) return;

    // Destroy previous chart
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    const { days, tempsHigh, tempsLow, rainfall } = generateForecastData();

    const ctx = chartRef.current.getContext('2d');

    // Create gradient for temperature area
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

    chartInstanceRef.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: days,
        datasets: [
          {
            type: 'line',
            label: 'Nhiệt độ cao',
            data: tempsHigh,
            borderColor: '#f97316',
            backgroundColor: 'transparent',
            tension: 0.4,
            pointRadius: 4,
            pointBackgroundColor: '#f97316',
            yAxisID: 'y',
            order: 1
          },
          {
            type: 'line',
            label: 'Nhiệt độ thấp',
            data: tempsLow,
            borderColor: '#3b82f6',
            backgroundColor: gradient,
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: '#3b82f6',
            yAxisID: 'y',
            order: 2
          },
          {
            type: 'bar',
            label: 'Lượng mưa (mm)',
            data: rainfall,
            backgroundColor: 'rgba(59, 130, 246, 0.5)',
            borderColor: '#3b82f6',
            borderWidth: 1,
            borderRadius: 4,
            yAxisID: 'y1',
            order: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: '#94a3b8',
              usePointStyle: true,
              padding: 20,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#f1f5f9',
            bodyColor: '#94a3b8',
            borderColor: '#334155',
            borderWidth: 1,
            padding: 12,
            displayColors: true,
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                if (context.parsed.y !== null) {
                  if (context.datasetIndex < 2) {
                    label += context.parsed.y + '°C';
                  } else {
                    label += context.parsed.y + ' mm';
                  }
                }
                return label;
              }
            }
          }
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            title: {
              display: true,
              text: 'Nhiệt độ (°C)',
              color: '#94a3b8',
              font: {
                size: 12
              }
            },
            grid: {
              color: 'rgba(148, 163, 184, 0.1)',
              drawBorder: false
            },
            ticks: {
              color: '#94a3b8',
              callback: function(value) {
                return value + '°C';
              }
            },
            min: 15,
            max: 40
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            title: {
              display: true,
              text: 'Lượng mưa (mm)',
              color: '#94a3b8',
              font: {
                size: 12
              }
            },
            grid: {
              drawOnChartArea: false
            },
            ticks: {
              color: '#94a3b8',
              callback: function(value) {
                return value + ' mm';
              }
            },
            min: 0,
            max: 50
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#94a3b8',
              font: {
                size: 11
              }
            }
          }
        }
      }
    });

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, [districtData]);

  return (
    <div className="w-full" style={{ height: '300px' }}>
      <canvas ref={chartRef}></canvas>
    </div>
  );
}

export default ForecastChart;
