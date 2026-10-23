with open('frontend/src/pages/Submit.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. queryKey submissions refetchOnMount
text = text.replace(
    'queryKey: ["submissions"],\n    queryFn: () => getSubmissions(20),',
    'queryKey: ["submissions"],\n    queryFn: () => getSubmissions(20),\n    refetchOnMount: "always",'
)
# If CRLF
text = text.replace(
    'queryKey: ["submissions"],\r\n    queryFn: () => getSubmissions(20),',
    'queryKey: ["submissions"],\r\n    queryFn: () => getSubmissions(20),\r\n    refetchOnMount: "always",'
)

# 2. invalidate review-queue
text = text.replace(
    'queryClient.invalidateQueries({ queryKey: ["overview"] })',
    'queryClient.invalidateQueries({ queryKey: ["overview"] })\n      queryClient.invalidateQueries({ queryKey: ["review-queue"] })'
)

# 3. length check in handleSubmit
old_hs = '''    if (!trimmed) {
      toast.error("Please enter complaint text before submitting.")
      return
    }'''

new_hs = '''    if (!trimmed) {
      toast.error("Please enter complaint text before submitting.")
      return
    }
    if (trimmed.length > 10000) {
      toast.error("Complaint text is too long (maximum 10,000 characters).")
      return
    }'''
text = text.replace(old_hs, new_hs)

# 4. Resolved status badge in table
old_badge = '''                        {row.needs_review ? (
                          <Badge variant="outline" className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 text-[10px]">
                            Flagged
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-[10px]">
                            Valid
                          </Badge>
                        )}'''

new_badge = '''                        {row.resolved ? (
                          <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-[10px]">
                            Resolved
                          </Badge>
                        ) : row.needs_review ? (
                          <Badge variant="outline" className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 text-[10px]">
                            Pending Review
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 text-[10px]">
                            Valid
                          </Badge>
                        )}'''
text = text.replace(old_badge, new_badge)

with open('frontend/src/pages/Submit.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
print("Submit.tsx updated!")

# Update ReviewQueue.tsx
with open('frontend/src/pages/ReviewQueue.tsx', 'r', encoding='utf-8') as f:
    rq_text = f.read()

rq_text = rq_text.replace(
    'queryKey: ["review-queue"],\n    queryFn: getReviewQueue,',
    'queryKey: ["review-queue"],\n    queryFn: getReviewQueue,\n    refetchOnMount: "always",\n    staleTime: 0,'
)
rq_text = rq_text.replace(
    'queryKey: ["review-queue"],\r\n    queryFn: getReviewQueue,',
    'queryKey: ["review-queue"],\r\n    queryFn: getReviewQueue,\r\n    refetchOnMount: "always",\r\n    staleTime: 0,'
)

with open('frontend/src/pages/ReviewQueue.tsx', 'w', encoding='utf-8') as f:
    f.write(rq_text)
print("ReviewQueue.tsx updated!")
