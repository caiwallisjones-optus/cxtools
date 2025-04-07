
  async function handleAudioLookup(actionName) {
    const audioName = document.querySelector(`input[name="${actionName}"]`).value;

    // Query the audio file details
    const response = await fetch(`/services/audio/query?name=${encodeURIComponent(audioName)}`);
    if (!response.ok) {
      alert('Failed to fetch audio details.');
      return;
    }

    const audioDetails = await response.json();
    console.log(audioDetails);
    const newUtterance = prompt(
      `File name: ${audioDetails.name}\n\nWording:\n${audioDetails.description}\n\Updatre wording:`,
      audioDetails.description
    );

    if (newUtterance !== null) {
      // Update the audio file with the new utterance
      const updateResponse = await fetch('/services/audio/update', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: audioName, utterance: newUtterance }),
      });

      if (updateResponse.ok) {
        alert('Audio updated successfully.');
      } else {
        alert('Failed to update audio.');
      }
    }
  }
