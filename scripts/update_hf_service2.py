path = r"c:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion\backend\app\services\hf_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

old_post = '''                            res = await client.post(
                                hub_url,
                                json={"inputs": request.prompt, "parameters": {"max_new_tokens": request.max_tokens}},
                                headers={"Authorization": f"Bearer {token}"}
                            )'''

new_post = '''                            payload = {"inputs": request.prompt}
                            if not any(k in model_id.lower() for k in ["bert", "roberta", "deberta"]):
                                payload["parameters"] = {"max_new_tokens": request.max_tokens}
                            res = await client.post(
                                hub_url,
                                json=payload,
                                headers={"Authorization": f"Bearer {token}"}
                            )'''

if old_post.replace("\n", "\r\n") in text:
    text = text.replace(old_post.replace("\n", "\r\n"), new_post.replace("\n", "\r\n"))
elif old_post in text:
    text = text.replace(old_post, new_post)
else:
    print("Old post not found!")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated hf_service.py post payload successfully!")
