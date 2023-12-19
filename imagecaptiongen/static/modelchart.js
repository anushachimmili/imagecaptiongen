var ctx = document.getElementById('myChart').getContext('2d');
          var myChart = new Chart(ctx, {
              type: 'bar',
              plugins: [ChartDataLabels],
              data: {
                  labels: ['BLIP', 'GIT'],
                  datasets: [{
                      label: 'Average Rating',
                      data: [blipAvg, gitAvg],
                      backgroundColor: ['#8e6f96','#028090'],
                      borderColor: ['#8e6f96','#028090'],
                      borderWidth: 1,
                      barPercentage: 0.7, 
                      categoryPercentage: 0.5, 
                  }]
              },
              options: {
                  plugins: {
                      datalabels: {
                          color: '#000',
                          anchor: 'end',
                          align: 'top',
                          formatter: function(value, context) {
                                return value.toFixed(1);
                            },
                          font: {
                              size: 14,
                          }
                      },
                      legend: {
                          display: false // This will align the legend to the right
                      },
                      title: {
                        display: true,
                        text: 'Average User Ratings by Model',
                        font: {
                            size: 14,
                        },
                        padding: {
                            bottom: 50
                        }
                    },
                  },
                  scales: {
                      x: {
                          grid: {
                              display: false,
                          },
                          ticks: {
                              font: {
                                  size : 12,
                                  weight: 'bold'
                              }
                          },
                      },
                      y: {
                          beginAtZero: true,
                          grid: {
                              display: false
                          },
                          ticks: {
                             stepSize: 1,
                              display: true,
                              font: {
                                  size : 12,
                              }
                          },
                          max: 5 
                      }
                  }
              }
          });