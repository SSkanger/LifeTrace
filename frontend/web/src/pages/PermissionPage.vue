<template>
<section class="page" id="permissionPage">
        <div class="section-title">
          <h2>权限与隐私</h2><span>用户可控</span>
        </div>
        <div class="card gold">
          <div class="card-title">只整理你授权的数据 <span class="badge">本地优先</span></div>
          <p>LifeTrace 会尽量在本地完成整理；当权限不足时，会明确说明缺少哪些线索，不会编造记忆。</p>
        </div>
        <div class="card" style="margin-top:12px">
          <div class="permission-row">
            <div>
              <div class="perm-title">照片与视频元数据</div>
              <div class="perm-sub">用于识别时间、地点和生活片段，不上传原图</div>
            </div>
            <div class="toggle on"></div>
          </div>
          <div class="permission-row">
            <div>
              <div class="perm-title">位置停留记录</div>
              <div class="perm-sub">用于判断图书馆、教学楼、操场等场景</div>
            </div>
            <div class="toggle on"></div>
          </div>
          <div class="permission-row">
            <div>
              <div class="perm-title">日程与课程表</div>
              <div class="perm-sub">用于解释当天活动，不读取私人备注</div>
            </div>
            <div class="toggle on"></div>
          </div>
          <div class="permission-row">
            <div>
              <div class="perm-title">App 使用线索</div>
              <div class="perm-sub">用于判断学习/休息状态，可随时关闭</div>
            </div>
            <div class="toggle"></div>
          </div>
        </div>
        <div class="grid-2" style="margin-top:13px"><button class="secondary" data-go="stateErrorPage">查看缺失状态</button><button class="primary" data-go="homePage">完成</button></div>
      </section>
</template>
