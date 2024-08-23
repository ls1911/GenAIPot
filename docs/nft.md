# Mint Your NFT Now!

We will create a wallet and mint the NFT to it. You will get details on how to claim it by email.

<form id="mintForm">
    <label for="email">Email:</label>
    <input type="email" id="email" name="email" required>
    <button type="submit">Mint NFT</button>
</form>

<div id="response"></div>

<script>
    document.getElementById('mintForm').addEventListener('submit', async function(event) {
        event.preventDefault();
        const email = document.getElementById('email').value;

        try {
            const response = await fetch('https://api.github.com/repos/ls1911/GenAIPot/actions/workflows/mint-nft.yml/dispatches', {
                method: 'POST',
                headers: {
                    'Accept': 'application/vnd.github.v3+json',
                    'Authorization': `Bearer YOUR_PERSONAL_ACCESS_TOKEN`,  // Use your GitHub PAT with workflow scope here
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    "ref": "main",
                    "inputs": {
                        "email": email
                    }
                })
            });

            if (!response.ok) {
                const errorDetails = await response.json();
                document.getElementById('response').textContent = `Error: ${errorDetails.message}`;
                alert(`Error: ${errorDetails.message}`);
            } else {
                const result = await response.json();
                document.getElementById('response').textContent = JSON.stringify(result, null, 2);
                alert('Minting request submitted successfully!');
            }
        } 
        catch (error) {
            document.getElementById('response').textContent = `Request failed: ${error.message}. Input email: ${email}`;
        }
    });
</script>
