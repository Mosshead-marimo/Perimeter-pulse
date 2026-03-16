import api from "../api/client";

export default function UploadBox() {
    const upload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        await api.post("/dashboard/upload", formData);
        alert("Analysis started");
    };

    return (
        <div className="card">
            <input type="file" onChange={upload} />
        </div>
    );
}
