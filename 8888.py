def university_admission(uni_name, major, score_line, admission_num, *teachers, **applicants):
    applicant_scores = {name: int(score) for name, score in applicants.items()}
    total_applicants = len(applicant_scores)
    qualified_applicants = {
        name: score for name, score in applicant_scores.items() if score >= score_line}
    qualified_num = len(qualified_applicants)
    sorted_qualified = sorted(
        qualified_applicants.items(), key=lambda x: x[1], reverse=True)
    admitted_list = [name for name, score in sorted_qualified[:admission_num]]
    admitted_num = len(admitted_list)
    print(f"大学名称: {uni_name}")
    print(f"专业: {major}")
    print(f"招生分数线: {score_line}")
    print(f"招生人数: {admission_num}")
    print(f"招生老师名单: {list(teachers)}")
    print(f"报考考生及其高考成绩: {applicant_scores}")
    print(f"报考人数: {total_applicants}")
    print(f"达线人数: {qualified_num}")
    print(f"录取名单: {admitted_list}")
    print(f"录取人数: {admitted_num}")


university_admission(
    '西北大学',
    '计算机科学',
    550,
    2,
    '张老师',
    '王老师',
    '李老师',
    张旭='540',
    李阳='575',
    王强='583',
    徐增='569',
    齐飞='557'
)
