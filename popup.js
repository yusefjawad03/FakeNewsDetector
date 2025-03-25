document.addEventListener('DOMContentLoaded', () => {
    const scanButton = document.getElementById('scan-button');
    const submitButton = document.getElementById('submit-button');
    const outputTextArea = document.getElementById('output');
    let reputationCircle = null;
    let styleCircle = null;
    let factCircle = null;

    //SCAN BUTTON
    scanButton.addEventListener('click', () => {
      chrome.runtime.sendMessage({ action: 'scan' }, (response) => {
        outputTextArea.value = response.text;
        scanButton.style.display = 'none';
        submitButton.style.display = 'block';
      });
    });
  
    //SUBMIT BUTTON
    submitButton.addEventListener('click', () => {
      const userInput = outputTextArea.value;
      let styleScore=null;
      submit.classList.add('hidden');
      showSpinner();
      
      chrome.runtime.sendMessage({ action: 'processText', userInput }, (response) => {
        while(!response){
        }
        styleScore = Number(response.style_score);
        reputationScore = Number(response.reputation_score);
        factScore = Number(response.fact_score);
        hideSpinner();
        results.classList.remove('hidden');
        results.style.display = 'flex';
        if (!styleCircle) {
          styleCircle = createCircle("#style-container", "Style Score");
        }
        if (!reputationCircle) {
          reputationCircle = createCircle("#reputation-container", "Reputation Score");
        }
        if (!factCircle) {
          factCircle = createCircle("#fact-container", "Fact Score");
        }
        styleCircle.animate(styleScore / 10);
        reputationCircle.animate(reputationScore / 10);
        factCircle.animate(factScore / 10);
      });

    });

    //ANIMATION FUNCTIONS
    function showSpinner() {
      const loadingSpinner = document.getElementById('loading-spinner');
      loadingSpinner.classList.add('active');
    }

    function hideSpinner() {
      const loadingSpinner = document.getElementById('loading-spinner');
      loadingSpinner.classList.remove('active');
    }

    function createCircle(container, type){
      return new ProgressBar.Circle(container, {
          color: '#007bff',
          strokeWidth: 4,
          trailColor: '#eee',
          trailWidth: 1,
          easing: 'easeInOut',
          duration: 1400,
          text: {
            autoStyleContainer: true,
          },
          from: { color: '#aaa', width: 1 },
          to: { color: '#007bff', width: 4 },
          step: function(state, circle) {
              circle.path.setAttribute('stroke', state.color);
              circle.path.setAttribute('stroke-width', state.width);

              let value = Math.round(circle.value() * 100);
              let textColor;

              if (value < 50) {
                  textColor = 'red';
              } else if (value === 50) {
                  textColor = 'black';
              } else {
                  textColor = 'green';
              }
              if (value === 0) {
                  circle.setText('');
              } else {
                circle.setText(`<div style="text-align: center; line-height: 1.2em;">${type}<br><span style="color: ${textColor};">${value}%</span></div>`);
              }

          }
      });
  }
});