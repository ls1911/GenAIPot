# Mint Your NFT Now !

We will create wallet and mint the NFT to it, you will get details how to claim it by email.

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

        const response = await fetch('https://api.github.com/repos/ls1911/GenAIPot/actions/workflows/nft.yml/dispatches', {
            method: 'POST',
            headers: {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': `token YOUR_GITHUB_PERSONAL_ACCESS_TOKEN`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                "ref": "main",
                "inputs": {
                    "email": email
                }
            })
        });

        const result = await response.json();
        document.getElementById('response').textContent = JSON.stringify(result, null, 2);
    });
</script>
