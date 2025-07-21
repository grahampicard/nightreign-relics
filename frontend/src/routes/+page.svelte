<script>
	let files;
	let jsonData = null;

	async function upload(event) {
		const file = event.target.files[0];
		if (!file) return;

		const formData = new FormData();
		formData.append("video", file);

		const response = await fetch("/extract-relics/", {
			method: "POST",
			body: formData,
		});

		if (response.ok) {
			jsonData = await response.json();
		}
	}

	function jsonToCsv(relics) {
		const headers = ["Relic", "Attribute 1", "Attribute 2", "Attribute 3"];
		const csvRows = [headers.join(",")];

		for (const item of relics) {
			const relic = `"${item.relic || ""}"`;
			const attributes = item.attributes.map(attr => `"${attr}"`);
			const paddedAttributes = Array(3).fill("");
			for (let i = 0; i < Math.min(attributes.length, 3); i++) {
				paddedAttributes[i] = attributes[i];
			}
			csvRows.push([relic, ...paddedAttributes].join(","));
		}

		return csvRows.join("\n");
	}

	function download() {
		if (!jsonData || !jsonData.relics) return;

		const csvContent = jsonToCsv(jsonData.relics);
		const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
		const link = document.createElement("a");
		const url = URL.createObjectURL(blob);
		link.setAttribute("href", url);
		link.setAttribute("download", "relics.csv");
		link.style.visibility = "hidden";
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	}
</script>

<div class="hero min-h-screen bg-base-200">
	<div class="hero-content text-center">
		<div class="max-w-md">
			<h1 class="text-5xl font-bold">Nightreign Relics</h1>
			<p class="py-6">Upload a video to extract the relics.</p>
			<input
				type="file"
				class="file-input file-input-bordered w-full max-w-xs"
				on:change={upload}
				accept=".mp4"
			/>
			{#if jsonData}
				<button class="btn btn-primary mt-4" on:click={download}
					>Download CSV</button
				>
			{/if}
		</div>
	</div>
</div>
